"""
API 專用的 request / response schema。
不修改 sec_10k_pipeline/models.py，避免污染核心資料結構。
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel
from sec_10k_pipeline.models import FilingOutput


class JobCreateRequest(BaseModel):
    cik: Optional[str] = None
    accession_number: Optional[str] = None
    url: Optional[str] = None


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    cache_hit: bool = False


class JobStatusResponse(BaseModel):
    job_id: str
    status: str                          # pending | running | done | failed
    result: Optional[FilingOutput] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


# ── 後台 Dashboard ───────────────────────────────────────────

class AdminStats(BaseModel):
    total_filings: int
    valid_count: int
    invalid_count: int
    avg_score: Optional[float] = None
    error_filings: int
    warning_filings: int
    avg_processing_ms: Optional[float] = None
    failed_jobs: int


class FilingListItem(BaseModel):
    accession_number: str
    company_name: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    parser_name: Optional[str] = None
    quality_score: Optional[float] = None
    quality_valid: Optional[bool] = None
    quality_errors: Optional[int] = None
    quality_warnings: Optional[int] = None
    processing_ms: Optional[int] = None
    fetched_at: str


class FilingListResponse(BaseModel):
    total: int
    items: list[FilingListItem]


# ── 規則分析 ④ ───────────────────────────────────────────────

class FlagCount(BaseModel):
    code: str
    severity: str
    count: int


class ItemFlagCount(BaseModel):
    item_number: str
    count: int


class ParserStat(BaseModel):
    parser_name: Optional[str] = None
    filings: int
    errors: int
    warnings: int
    avg_score: Optional[float] = None


class TimingAvg(BaseModel):
    fetch_html_sec: float
    preprocess_sec: float
    parse_sec: float
    postprocess_sec: float


class FlagAnalytics(BaseModel):
    by_code: list[FlagCount]
    by_item: list[ItemFlagCount]
    by_parser: list[ParserStat]
    timing: Optional[TimingAvg] = None
    total_flags: int


# ── 系統健康 ⑤ ───────────────────────────────────────────────

class JobSummary(BaseModel):
    job_id: str
    status: str
    accession_number: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class JobAnalytics(BaseModel):
    status_counts: dict[str, int]
    recent_failures: list[JobSummary]
