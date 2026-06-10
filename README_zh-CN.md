<div align="center">

# SEC 10-K 結構化抽取

**將原始 SEC EDGAR 申報文件轉換為結構化 JSON 與可讀 Markdown**

[English](README.md) | [中文](README_zh-CN.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-≥%203.10-blue)
![Node](https://img.shields.io/badge/node-≥%2018-green)

https://github.com/user-attachments/assets/02e51b12-4362-44bf-afa3-aca48c5852c0

</div>

---

SEC 10-K 申報文件出了名地難處理。原始 EDGAR 文件是格式不一的 HTML，各家公司的 Item 分界寫法都不同，而要從 XBRL 還原一張資產負債表，光是把數字和標籤對上就要同時解析三個 Linkbase 檔案。

這個專案提供一條解析 Pipeline 加上 Web UI，把這些麻煩全部包辦。送入任何 10-K 申報文件的網址，就能取回完整的結構化 JSON，每個 Item 都已標註並抽取完畢；也可以直接把 Item 8 財務報表渲染成 Markdown。

## 功能

- **完整 Item 抽取** — 自動拆分 Part I / II / III / IV，並將每個 Item 標註為 `extracted`、`incorporated_by_reference`、`not_applicable`、`reserved` 或 `missing`
- **XBRL 財報還原** — 解析 Instance + Presentation + Label Linkbase，重建 Item 8 主表（損益表、資產負債表、現金流量表等）
- **Markdown 渲染** — 輸出乾淨可讀的 Markdown，含數字附註與文字揭露
- **非同步 Job Queue** — 送出申報後立即拿到 `job_id`，背景處理完成後再輪詢取結果
- **Cache 機制** — 相同申報只處理一次，以 `accession_number` 為 key
- **雙輸入模式** — 支援 `cik + accession_number` 或直接給 EDGAR URL
- **Admin 面板** — Job 健康儀表板、Flag 統計分析、各 Parser 表現，以及支援懶加載的 Item 詳情側抽屜

## 快速開始

**環境需求：** Python ≥ 3.10、Node.js ≥ 18

```bash
# 後端
cd api
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000（互動式 API 文檔在 /docs）

# 前端（新開一個終端機）
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

**環境變數**

`api/.env`
```
DB_PATH=./data/sec_extraction.db
CORS_ORIGINS=http://localhost:5173
```

`frontend/.env`
```
VITE_API_BASE_URL=http://localhost:8000
```

## 使用方式

透過 Web UI 送出申報，或直接呼叫 API：

```bash
# 送出解析 Job
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"cik":"0000320193","accession_number":"0000320193-23-000106"}'
# → { "job_id": "...", "status": "pending", "cache_hit": false }
```

或直接在 Python 裡使用解析模組：
```
from api.sec_10k_pipeline.pipeline import Pipeline
from api.sec_10k_pipeline.models import FilingInput

pipeline = Pipeline()

# Option 1: CIK + Accession Number
result = pipeline.run(FilingInput(
    cik="0000320193",
    accession_number="0000320193-23-000106",
))

# Option 2: Direct URL
result = pipeline.run(FilingInput(
    url="https://www.sec.gov/Archives/edgar/data/.../filing.htm",
))

# Save results (JSON + Markdown)
result = pipeline.run(input, save_to="output/")
```

完整 API 文檔：[docs/api.md](docs/api.md)

## 技術選型

**後端：** FastAPI · SQLite (aiosqlite) · lxml / BeautifulSoup · Pydantic · asyncio

**前端：** Vue 3 · TypeScript · Vite · Pinia · shadcn-vue · Tailwind CSS v4

## 專案結構

```
api/                  # FastAPI 後端 + 解析 Pipeline
├── sec_10k_pipeline/ # 核心引擎（Regex、LLM 輔助、XBRL 解析）
└── ...
frontend/             # Vue 3 SPA
docs/                 # API 文檔、架構說明、驗證規則
```

## 貢獻

歡迎提 Issue 和 Pull Request。如果你遇到解析結果不正確的申報文件，或有想要的功能，開 Issue 是最好的起點 — 來自真實申報文件的邊界案例尤其有幫助。

1. Fork 此 repo 並建立分支
2. 修改程式碼，寫清楚的 commit message
3. 開 PR，說明改了什麼、為什麼改

## 授權

MIT — 詳見 [LICENSE](LICENSE)。
