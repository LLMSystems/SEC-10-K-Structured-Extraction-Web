"""
資料庫初始化與 schema 定義。
dev 用 SQLite；換 PostgreSQL 時只需改連線字串與 aiosqlite → asyncpg。
"""

from pathlib import Path
import os
import aiosqlite
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = Path(os.getenv("DB_PATH", "./data/sec_extraction.db"))

_CREATE_FILINGS = """
CREATE TABLE IF NOT EXISTS filings (
    accession_number TEXT PRIMARY KEY,
    result_json      TEXT NOT NULL,
    fetched_at       TEXT NOT NULL,
    processing_ms    INTEGER,
    parser_name      TEXT,
    quality_score    REAL,
    quality_valid    INTEGER,
    quality_errors   INTEGER,
    quality_warnings INTEGER
)
"""

# 既有 DB 用：CREATE TABLE IF NOT EXISTS 不會替舊表補欄位，
# 因此額外做一次冪等的 ALTER TABLE 補欄位（欄位已存在則跳過）。
_FILINGS_MIGRATIONS = {
    "parser_name":      "ALTER TABLE filings ADD COLUMN parser_name TEXT",
    "quality_score":    "ALTER TABLE filings ADD COLUMN quality_score REAL",
    "quality_valid":    "ALTER TABLE filings ADD COLUMN quality_valid INTEGER",
    "quality_errors":   "ALTER TABLE filings ADD COLUMN quality_errors INTEGER",
    "quality_warnings": "ALTER TABLE filings ADD COLUMN quality_warnings INTEGER",
}

_CREATE_JOBS = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id           TEXT PRIMARY KEY,
    status           TEXT NOT NULL DEFAULT 'pending',
    input_json       TEXT NOT NULL,
    accession_number TEXT,
    result_json      TEXT,
    error_message    TEXT,
    created_at       TEXT NOT NULL,
    completed_at     TEXT
)
"""

_CREATE_INDEXES = [
    """
    CREATE INDEX IF NOT EXISTS idx_filings_fetched_at
    ON filings(fetched_at)
    """,
    
    """
    CREATE INDEX IF NOT EXISTS idx_jobs_status
    ON jobs(status)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_jobs_created_at
    ON jobs(created_at)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_jobs_accession_number
    ON jobs(accession_number)
    """,
]


async def init_db(db_path: Path = DATABASE_URL) -> None:
    os.makedirs(db_path.parent, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(_CREATE_FILINGS)
        await db.execute(_CREATE_JOBS)
        await _migrate_filings(db)
        for index in _CREATE_INDEXES:
            await db.execute(index)
        await db.commit()


async def _migrate_filings(db: aiosqlite.Connection) -> None:
    """替既有 filings 表補上缺少的欄位（冪等）。"""
    async with db.execute("PRAGMA table_info(filings)") as cursor:
        existing = {row[1] for row in await cursor.fetchall()}
    for column, ddl in _FILINGS_MIGRATIONS.items():
        if column not in existing:
            await db.execute(ddl)
