# SEC 10-K Extraction API 文檔

## 快速啟動

```bash
uvicorn src.api.main:app --reload
# API 預設跑在 http://localhost:8000
# 互動式文檔：http://localhost:8000/docs
```

---

## 概覽

非同步 Job Queue 架構：送出請求後立即取得 `job_id`，再用 polling 查結果。

```
POST /jobs          送出解析請求 → 取得 job_id
GET  /jobs/{id}     輪詢 job 狀態與結果
GET  /filings/{acc} 直接查 cache（已完成才有）
```

**Cache 行為**：相同的 `accession_number` 只處理一次。重複送出時 `cache_hit=true`，`GET /jobs/{id}` 可立即取到結果。

---

## 端點

### `POST /jobs` — 送出解析請求

**Request Body**

支援兩種輸入方式，擇一：

| 方式 | 欄位 | 說明 |
|---|---|---|
| 方式一 | `cik` + `accession_number` | 標準輸入 |
| 方式二 | `url` | SEC EDGAR 主文件 URL，自動解析 CIK 與 Accession Number |

```json
// 方式一
{
  "cik": "0000320193",
  "accession_number": "0000320193-23-000106"
}

// 方式二
{
  "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm"
}
```

**Response** `202 Accepted`

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "pending",
  "cache_hit": false
}
```

| 欄位 | 說明 |
|---|---|
| `job_id` | 用來查詢結果的識別碼 |
| `status` | `pending`（排隊中）或 `done`（cache hit） |
| `cache_hit` | `true` 表示此 accession number 已有快取結果，可直接 `GET /jobs/{job_id}` 取結果 |

**Errors**

| 狀態碼 | 原因 |
|---|---|
| `422` | 未提供 `cik+accession_number` 也未提供 `url`；或 URL 格式無法解析 |

---

### `GET /jobs/{job_id}` — 查詢 Job 狀態與結果

**Response** `200 OK`

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "done",
  "result": { ...FilingOutput... },
  "error": null,
  "created_at": "2026-05-12T10:00:00.123456+00:00",
  "completed_at": "2026-05-12T10:00:01.456789+00:00"
}
```

| 欄位 | 說明 |
|---|---|
| `status` | `pending` / `running` / `done` / `failed` |
| `result` | `status=done` 時有值，否則 `null`；結構見 [FilingOutput](#filingoutput) |
| `error` | `status=failed` 時有值，錯誤訊息字串 |
| `created_at` | Job 建立時間（ISO 8601 UTC） |
| `completed_at` | 完成時間；`pending`/`running` 時為 `null` |

**Polling 建議**：每 1 秒查一次，`status` 變為 `done` 或 `failed` 時停止。平均處理時間約 0.7 秒。

**Errors**

| 狀態碼 | 原因 |
|---|---|
| `404` | `job_id` 不存在 |

---

### `GET /filings/{accession_number}` — 直接查 Cache

bypass Job 系統，直接回傳已快取的 `FilingOutput`。適合確定已處理過、想快速取原始結果的場景。

**Path Parameter**

`accession_number`：格式為 `XXXXXXXXXX-YY-ZZZZZZ`，例如 `0000320193-23-000106`

**Response** `200 OK`

直接回傳 [FilingOutput](#filingoutput) 物件。

**Errors**

| 狀態碼 | 原因 |
|---|---|
| `404` | 此 accession number 尚未處理過，或不在 cache 中；**不會**自動觸發處理 |

---

## 資料結構

### FilingOutput

```json
{
  "filing_info": {
    "cik": "0000320193",
    "accession_number": "0000320193-23-000106",
    "company_name": "Apple Inc.",
    "fiscal_year_end": "2023-09-30",
    "filer_category": "Large accelerated filer"
  },
  "items": [
    {
      "part": "Part I",
      "item_number": "1",
      "item_title": "Business",
      "content_text": "Apple Inc. designs, manufactures...",
      "char_range": [1024, 45231],
      "status": "extracted"
    },
    {
      "part": "Part III",
      "item_number": "10",
      "item_title": "Directors, Executive Officers and Corporate Governance",
      "content_text": null,
      "char_range": null,
      "status": "incorporated_by_reference"
    }
  ],
  "timing": {
    "fetch_html_sec": 0.159,
    "preprocess_sec": 0.494,
    "parse_sec": 0.035,
    "postprocess_sec": 0.012
  }
}
```

#### Item Status 說明

| Status | 說明 |
|---|---|
| `extracted` | 成功抽取內容，`content_text` 有值 |
| `incorporated_by_reference` | 以引用方式指向其他文件（常見於 Part III） |
| `not_applicable` | 公司明確表示不適用（如 Item 4 礦安全） |
| `reserved` | SEC 規定保留（Item 6 於 2021 年後） |
| `missing` | Parser 找不到此 Item，可能需人工確認 |

---

## 完整使用範例

### 方式一：CIK + Accession Number

```bash
# 1. 送出請求
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"cik":"0000320193","accession_number":"0000320193-23-000106"}'

# → {"job_id":"3fa85f64-...","status":"pending","cache_hit":false}

# 2. 輪詢結果
curl http://localhost:8000/jobs/3fa85f64-...

# → {"status":"done","result":{...},...}
```

### 方式二：直接給 URL

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm"}'
```

### Cache Hit（相同 accession number 第二次送）

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"cik":"0000320193","accession_number":"0000320193-23-000106"}'

# → {"job_id":"new-uuid","status":"done","cache_hit":true}
# 可以直接 GET /jobs/{new-uuid} 取結果，不需等待
```

### Python 範例

```python
import httpx
import time

BASE_URL = "http://localhost:8000"

def extract_10k(cik: str, accession_number: str) -> dict:
    # 送出請求
    resp = httpx.post(f"{BASE_URL}/jobs", json={
        "cik": cik,
        "accession_number": accession_number,
    })
    resp.raise_for_status()
    job = resp.json()

    # cache hit：直接取結果
    if job["cache_hit"]:
        result = httpx.get(f"{BASE_URL}/jobs/{job['job_id']}")
        return result.json()["result"]

    # 輪詢直到完成
    while True:
        result = httpx.get(f"{BASE_URL}/jobs/{job['job_id']}").json()
        if result["status"] == "done":
            return result["result"]
        if result["status"] == "failed":
            raise RuntimeError(f"Job failed: {result['error']}")
        time.sleep(1)

output = extract_10k("0000320193", "0000320193-23-000106")
print(output["filing_info"]["company_name"])  # Apple Inc.
```

---

## 環境變數

| 變數 | 預設值 | 說明 |
|---|---|---|
| `DB_PATH` | `./data/sec_extraction.db` | SQLite 資料庫路徑 |
