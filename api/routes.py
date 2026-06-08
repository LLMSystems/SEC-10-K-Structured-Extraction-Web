"""
路由定義：POST /jobs, GET /jobs/{job_id}, GET /filings/{accession_number},
         POST /xbrl-markdown
queue 和 cache 由 main.py 在 lifespan 啟動時注入。
"""

from __future__ import annotations
import asyncio
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from fastapi import Query

from models.job import (
    JobCreateRequest,
    JobCreateResponse,
    JobStatusResponse,
    AdminStats,
    FilingListResponse,
    FlagAnalytics,
    JobAnalytics,
)
from cache import CacheService
from sec_10k_pipeline.models import FilingInput, FilingOutput, ItemResult
from utils import parse_sec_url
from item8_markdown import get_item8_markdown

logger = logging.getLogger(__name__)
router = APIRouter()

_queue: Optional[asyncio.Queue] = None
_cache: Optional[CacheService] = None


def init_routes(queue: asyncio.Queue, cache: CacheService) -> None:
    global _queue, _cache
    _queue = queue
    _cache = cache


@router.post("/jobs", response_model=JobCreateResponse, status_code=202)
async def create_job(req: JobCreateRequest):
    try:
        # 如果有 req.cik、req.accession_number 就用它們；否則嘗試從 req.url 解析。後者適合直接給 URL 的場景（P1）。
        print(f"Received job request: {req}")
        if req.cik and req.accession_number:
            filing_input = FilingInput(
                cik=req.cik,
                accession_number=req.accession_number,
                url=req.url,
            )
        elif req.url:
            cik, accession = await parse_sec_url(req.url)
            filing_input = FilingInput(
                cik=cik,
                accession_number=accession,
                url=None,
            )
        else:
            raise HTTPException(status_code=422, detail="Either cik+accession_number or url must be provided")
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    job_id = str(uuid.uuid4())
    accession_number = filing_input.accession_number
    input_json = filing_input.model_dump_json()

    # cache hit：已有結果，直接建 done job，不進 queue
    if accession_number:
        cached = await _cache.get_filing(accession_number)
        if cached is not None:
            await _cache.create_job_done(
                job_id, input_json, accession_number, cached.model_dump_json()
            )
            return JobCreateResponse(job_id=job_id, status="done", cache_hit=True)

    await _cache.create_job(job_id, input_json, accession_number)
    await _queue.put({
        "job_id": job_id,
        "input_json": input_json,
        "accession_number": accession_number,
    })

    return JobCreateResponse(job_id=job_id, status="pending", cache_hit=False)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str):
    job = await _cache.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    result: Optional[FilingOutput] = None
    if job["status"] == "done" and job.get("result_json"):
        result = FilingOutput.model_validate_json(job["result_json"])

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        result=result,
        error=job.get("error_message"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at"),
    )


@router.get("/admin/stats", response_model=AdminStats)
async def admin_stats():
    """後台 KPI 彙總。"""
    return await _cache.get_filings_stats()


@router.get("/admin/filings", response_model=FilingListResponse)
async def admin_filings(
    sort: str = Query("score_asc", pattern="^(score_asc|score_desc|recent)$"),
    only: str = Query("all", pattern="^(all|errors|invalid)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """後台待審佇列：列出 filings 與品質彙總，預設最低分優先。"""
    return await _cache.list_filings(sort=sort, only=only, limit=limit, offset=offset)


@router.get("/admin/flag-stats", response_model=FlagAnalytics)
async def admin_flag_stats():
    """④ 規則分析：flag 頻率、parser 彙總、平均各階段耗時。"""
    return await _cache.get_flag_analytics()


@router.get("/admin/job-stats", response_model=JobAnalytics)
async def admin_job_stats(failures_limit: int = Query(20, ge=1, le=100)):
    """⑤ 系統健康：job 狀態分佈與最近失敗清單。"""
    return await _cache.get_job_analytics(failures_limit=failures_limit)


@router.get("/filings/{accession_number}/items/{item_number}", response_model=ItemResult)
async def get_filing_item(accession_number: str, item_number: str):
    """取得單一 item 的完整內容（含 content_text），供前端 lazy load 使用。"""
    result = await _cache.get_filing(accession_number)
    if result is None:
        raise HTTPException(status_code=404, detail="Filing not found in cache")
    for item in result.items:
        if item.item_number == item_number:
            return item
    raise HTTPException(status_code=404, detail=f"Item {item_number} not found")


@router.get("/filings/{accession_number}", response_model=FilingOutput)
async def get_filing(
    accession_number: str,
    strip_content: bool = Query(False, description="若為 true，移除所有 item 的 content_text 以減少傳輸大小"),
):
    """直接查 cache，bypass job 系統。cache miss 時回 404，不觸發處理。"""
    result = await _cache.get_filing(accession_number)
    if result is None:
        raise HTTPException(status_code=404, detail="Filing not found in cache")
    if strip_content:
        result = result.model_copy(update={
            "items": [
                item.model_copy(update={"content_text": None})
                for item in result.items
            ]
        })
    return result


class XbrlMarkdownRequest(BaseModel):
    cik: str
    accession_number: str

@router.post("/xbrl-markdown", response_class=PlainTextResponse)
async def create_xbrl_markdown(req: XbrlMarkdownRequest):
    """
    同步擷取 SEC XBRL 資料並渲染為 Markdown。
    直接返回 text/plain，適合快速預覽或下載。
    """
    try:
        markdown = await asyncio.to_thread(
            get_item8_markdown,
            req.cik,
            req.accession_number,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("xbrl-markdown failed for %s / %s", req.cik, req.accession_number)
        raise HTTPException(status_code=500, detail=str(exc))
    return PlainTextResponse(content=markdown, media_type="text/markdown; charset=utf-8")
