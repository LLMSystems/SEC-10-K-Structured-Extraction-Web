"""
CacheService：封裝所有 DB 讀寫操作。
jobs table 追蹤請求狀態；filings table 存解析結果 cache。
"""

from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite

from db import DATABASE_URL
from sec_10k_pipeline.models import FilingOutput


class CacheService:
    def __init__(self, db_path: Path = DATABASE_URL):
        self.db_path = db_path

    # ── filings ──────────────────────────────────────────────

    async def get_filing(self, accession_number: str) -> Optional[FilingOutput]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT result_json FROM filings WHERE accession_number = ?",
                (accession_number,),
            ) as cursor:
                row = await cursor.fetchone()
                return FilingOutput.model_validate_json(row[0]) if row else None

    async def save_filing(
        self,
        accession_number: str,
        result: FilingOutput,
        processing_ms: int,
    ) -> None:
        q = result.quality
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO filings
                    (accession_number, result_json, fetched_at, processing_ms,
                     parser_name, quality_score, quality_valid,
                     quality_errors, quality_warnings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    accession_number,
                    result.model_dump_json(),
                    datetime.now(timezone.utc).isoformat(),
                    processing_ms,
                    q.parser_name if q else None,
                    q.score if q else None,
                    int(q.is_valid) if q else None,
                    q.counts.get("error", 0) if q else None,
                    q.counts.get("warning", 0) if q else None,
                ),
            )
            await db.commit()

    # ── admin / dashboard ────────────────────────────────────

    async def get_filings_stats(self) -> dict:
        """後台 KPI：filings 品質彙總 + job 失敗數。"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT
                    COUNT(*) AS total_filings,
                    COALESCE(SUM(CASE WHEN quality_valid = 1 THEN 1 ELSE 0 END), 0) AS valid_count,
                    COALESCE(SUM(CASE WHEN quality_valid = 0 THEN 1 ELSE 0 END), 0) AS invalid_count,
                    AVG(quality_score) AS avg_score,
                    COALESCE(SUM(CASE WHEN quality_errors   > 0 THEN 1 ELSE 0 END), 0) AS error_filings,
                    COALESCE(SUM(CASE WHEN quality_warnings > 0 THEN 1 ELSE 0 END), 0) AS warning_filings,
                    AVG(processing_ms) AS avg_processing_ms
                FROM filings
                """
            ) as cursor:
                stats = dict(await cursor.fetchone())

            async with db.execute(
                "SELECT COUNT(*) AS c FROM jobs WHERE status = 'failed'"
            ) as cursor:
                stats["failed_jobs"] = (await cursor.fetchone())["c"]

        return stats

    # 白名單，避免 ORDER BY 注入。NULL 分數一律排到最後。
    _SORT_CLAUSES = {
        "score_asc":  "quality_score IS NULL, quality_score ASC",
        "score_desc": "quality_score IS NULL, quality_score DESC",
        "recent":     "fetched_at DESC",
    }

    async def list_filings(
        self,
        sort: str = "score_asc",
        only: str = "all",
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """後台待審佇列：列出 filings + 品質欄位（company_name 從 result_json 取）。"""
        where = ""
        if only == "errors":
            where = "WHERE quality_errors > 0"
        elif only == "invalid":
            where = "WHERE quality_valid = 0"

        order = self._SORT_CLAUSES.get(sort, self._SORT_CLAUSES["score_asc"])

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                f"SELECT COUNT(*) AS c FROM filings {where}"
            ) as cursor:
                total = (await cursor.fetchone())["c"]

            async with db.execute(
                f"""
                SELECT
                    accession_number,
                    json_extract(result_json, '$.filing_info.company_name')   AS company_name,
                    json_extract(result_json, '$.filing_info.fiscal_year_end') AS fiscal_year_end,
                    parser_name,
                    quality_score,
                    quality_valid,
                    quality_errors,
                    quality_warnings,
                    processing_ms,
                    fetched_at
                FROM filings
                {where}
                ORDER BY {order}
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ) as cursor:
                rows = [dict(r) for r in await cursor.fetchall()]

        return {"total": total, "items": rows}

    async def get_flag_analytics(self) -> dict:
        """④ 規則分析：flag 頻率（by code / by item）、parser 彙總、平均各階段耗時。"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # parser 彙總走欄位（便宜）
            async with db.execute(
                """
                SELECT
                    parser_name,
                    COUNT(*) AS filings,
                    COALESCE(SUM(quality_errors), 0)   AS errors,
                    COALESCE(SUM(quality_warnings), 0) AS warnings,
                    AVG(quality_score) AS avg_score
                FROM filings
                GROUP BY parser_name
                ORDER BY filings DESC
                """
            ) as cursor:
                by_parser = [dict(r) for r in await cursor.fetchall()]

            # flags / timing 埋在 result_json，逐筆 parse（cache 規模小，足夠）
            async with db.execute("SELECT result_json FROM filings") as cursor:
                rows = await cursor.fetchall()

        code_counter: Counter = Counter()
        code_severity: dict[str, str] = {}
        item_counter: Counter = Counter()
        timing_sum = {"fetch_html_sec": 0.0, "preprocess_sec": 0.0,
                      "parse_sec": 0.0, "postprocess_sec": 0.0}
        timing_n = 0
        total_flags = 0

        for (result_json,) in rows:
            try:
                data = json.loads(result_json)
            except (json.JSONDecodeError, TypeError):
                continue

            quality = data.get("quality")
            if quality:
                for flag in quality.get("flags", []):
                    code = flag.get("code", "unknown")
                    code_counter[code] += 1
                    code_severity[code] = flag.get("severity", "info")
                    if flag.get("item_number"):
                        item_counter[flag["item_number"]] += 1
                    total_flags += 1

            timing = data.get("timing")
            if timing:
                for key in timing_sum:
                    timing_sum[key] += timing.get(key, 0.0) or 0.0
                timing_n += 1

        by_code = [
            {"code": code, "severity": code_severity.get(code, "info"), "count": count}
            for code, count in code_counter.most_common()
        ]
        by_item = [
            {"item_number": item, "count": count}
            for item, count in sorted(
                item_counter.items(), key=lambda kv: kv[1], reverse=True
            )
        ]
        timing = (
            {key: round(value / timing_n, 3) for key, value in timing_sum.items()}
            if timing_n
            else None
        )

        return {
            "by_code": by_code,
            "by_item": by_item,
            "by_parser": by_parser,
            "timing": timing,
            "total_flags": total_flags,
        }

    async def get_job_analytics(self, failures_limit: int = 20) -> dict:
        """⑤ 系統健康：job 狀態分佈 + 最近失敗清單。"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT status, COUNT(*) AS c FROM jobs GROUP BY status"
            ) as cursor:
                status_counts = {r["status"]: r["c"] for r in await cursor.fetchall()}

            async with db.execute(
                """
                SELECT job_id, status, accession_number, error_message,
                       created_at, completed_at
                FROM jobs
                WHERE status = 'failed'
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (failures_limit,),
            ) as cursor:
                recent_failures = [dict(r) for r in await cursor.fetchall()]

        return {"status_counts": status_counts, "recent_failures": recent_failures}

    # ── jobs ─────────────────────────────────────────────────

    async def create_job(
        self,
        job_id: str,
        input_json: str,
        accession_number: Optional[str],
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO jobs (job_id, status, input_json, accession_number, created_at)
                VALUES (?, 'pending', ?, ?, ?)
                """,
                (job_id, input_json, accession_number, _now()),
            )
            await db.commit()

    async def get_job(self, job_id: str) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_job_running(self, job_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE jobs SET status = 'running' WHERE job_id = ?", (job_id,)
            )
            await db.commit()

    async def update_job_done(self, job_id: str, result_json: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE jobs
                SET status = 'done', result_json = ?, completed_at = ?
                WHERE job_id = ?
                """,
                (result_json, _now(), job_id),
            )
            await db.commit()

    async def create_job_done(
        self,
        job_id: str,
        input_json: str,
        accession_number: str,
        result_json: str,
    ) -> None:
        """cache hit 專用：直接以 done 狀態建立 job，跳過 queue。"""
        now = _now()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO jobs
                    (job_id, status, input_json, accession_number, result_json, created_at, completed_at)
                VALUES (?, 'done', ?, ?, ?, ?, ?)
                """,
                (job_id, input_json, accession_number, result_json, now, now),
            )
            await db.commit()

    async def update_job_failed(self, job_id: str, error: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE jobs
                SET status = 'failed', error_message = ?, completed_at = ?
                WHERE job_id = ?
                """,
                (error, _now(), job_id),
            )
            await db.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
