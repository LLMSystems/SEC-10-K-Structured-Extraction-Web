# SEC 10-K Extraction API - 設計文檔

> **適用對象**：Demo
> **模式**：job queu）+ SQLite cache  
> **目標**：在現有 Async Pipeline 之上包一層 FastAPI

---

## 一、架構設計

```
Client
  │
  │ POST /jobs          → 建立 job，回傳 job_id
  │ GET  /jobs/{id}     → 查詢 job 狀態與結果
  │ GET  /filings/{acc} → 直接查 cache（已完成才有）
  │
  ▼
FastAPI App
  │
  ├── JobRouter          路由層，驗證輸入、查 cache、建 job
  │
  ├── JobQueue           asyncio.Queue（或 arq/celery，視需要擴展）
  │
  ├── Worker（background task）
  │     ├── AsyncPipeline    包現有 Pipeline，async fetch + executor parse
  │     └── CacheService     讀寫 SQLite/PostgreSQL
  │
  └── DB（SQLite dev / PostgreSQL prod）
        ├── jobs table       job_id, status, input, error, created_at
        └── filings table    accession_number, result_json, fetched_at
```

### 主要設計想法

1. **Cache key = accession number**：同一份 10-K 不管誰送、送幾次，只處理一次
2. **Job 與 Filing 分開存**：job 是「這次請求的追蹤記錄」；filing 是「處理結果的 cache」，兩者 1:1 或多:1（多個 job 對同一 filing）
3. **Worker 用 asyncio**：fetch 是 I/O bound，用 `httpx.AsyncClient` 讓多筆可以並發下載；parse/preprocess 是 CPU bound，丟進 `asyncio.get_event_loop().run_in_executor(None, ...)` 避免 block event loop

### 新增：`api/` 目錄

```
src/api/
├── __init__.py
├── main.py          FastAPI app 初始化、lifespan、middleware
├── routes.py        POST /jobs, GET /jobs/{id}, GET /filings/{acc}
├── models/job.py        API 專用的 request/response schema（不污染現有 models.py）
├── sec_10k_pipeline/    解析主程式
├── worker.py        background worker loop
├── cache.py         CacheService（DB 讀寫封裝）
└── db.py            SQLAlchemy / aiosqlite schema 定義
```

## 四、資料庫 Schema

```sql
-- 處理結果 cache
CREATE TABLE filings (
    accession_number TEXT PRIMARY KEY,
    result_json      TEXT NOT NULL,       -- FilingOutput.model_dump_json()
    fetched_at       TIMESTAMP NOT NULL,
    processing_ms    INTEGER             
);

-- Job 追蹤
CREATE TABLE jobs (
    job_id           TEXT PRIMARY KEY,    -- uuid4
    status           TEXT NOT NULL,       -- pending | running | done | failed
    input_json       TEXT NOT NULL,       -- FilingInput.model_dump_json()
    accession_number TEXT,                -- FK to filings（URL 模式為 NULL）
    error_message    TEXT,
    created_at       TIMESTAMP NOT NULL,
    completed_at     TIMESTAMP
);
```

---

## 五、API 端點設計

### `POST /jobs` — 送出解析請求

**Request body**（同現有 `FilingInput`）：
```json
{
  "cik": "0000320193",
  "accession_number": "0000320193-23-000106"
}
```

**Response**（立即回傳，不等處理完）：
```json
{
  "job_id": "3fa85f64-...",
  "status": "pending",
  "cache_hit": false          // true 表示已有結果，可直接 GET /jobs/{id}
}
```

**Cache hit 流程**：
```
收到請求
  → 有 accession_number？
      → 查 filings table
          → 有結果 → 建 job（status=done, accession_number 指過去結果）→ 回傳 cache_hit=true
          → 無結果 → 建 job（status=pending）→ 入 queue
```

### `GET /jobs/{job_id}` — 查詢狀態與結果

```json
{
  "job_id": "3fa85f64-...",
  "status": "done",
  "result": { ...FilingOutput... },   // status=done 才有
  "error": null,                       // status=failed 才有
  "created_at": "2026-05-12T10:00:00Z",
  "completed_at": "2026-05-12T10:00:01Z"
}
```

status 流程：`pending → running → done / failed`

### `GET /filings/{accession_number}` — 直接查 cache

快捷端點，bypass job 系統，直接回傳已完成的結果。若 cache miss 回 404（不自動觸發處理）。

---

## 六、並發安全：防止重複處理同一筆

同一個 accession number 同時收到兩個請求時，只能有一個 worker 在跑，另一個要等結果：

```python
# worker.py 中
_in_flight: dict[str, asyncio.Event] = {}

async def process_job(job):
    key = job.accession_number
    if key and key in _in_flight:
        await _in_flight[key].wait()   # 等第一個跑完
        # 第一個跑完後 cache 已有結果，直接撈
        return await cache.get(key)
    
    event = asyncio.Event()
    _in_flight[key] = event
    try:
        result = await pipeline.run_async(job.input)
        await cache.save(key, result)
        return result
    finally:
        event.set()
        _in_flight.pop(key, None)
```

---

## 七、實作順序（建議）
1. `AsyncPipeline`（async fetch + executor）
2. DB schema + `CacheService`
3. `POST /jobs` + `GET /jobs/{id}`
4. Background worker loo
5. Cache hit 邏輯、`GET /filings/{acc}`

---

## 十、快速驗證

實作完後，用以下指令驗證不 regression：

```bash
# 啟動 API
uvicorn src.api.main:app --reload

# 手動測試
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"cik":"0000320193","accession_number":"0000320193-23-000106"}'
```
