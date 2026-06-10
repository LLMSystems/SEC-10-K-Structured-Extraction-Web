<div align="center">

# SEC 10-K Structured Extraction

**Turn raw SEC EDGAR filings into clean structured JSON and readable Markdown**

[English](README.md) | [中文](README_zh-CN.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-≥%203.10-blue)
![Node](https://img.shields.io/badge/node-≥%2018-green)

https://github.com/user-attachments/assets/02e51b12-4362-44bf-afa3-aca48c5852c0

</div>

---

SEC 10-K filings are notoriously hard to work with. Raw EDGAR documents are inconsistent HTML, Item boundaries vary across filers, and reconstructing a balance sheet from XBRL means navigating three separate linkbase files just to get a number with a label.

This project provides a parsing pipeline + web UI that handles all of that. Submit any 10-K filing URL and get back structured JSON with every Item labeled and extracted — or render Item 8 financial statements directly to Markdown.

## Features

- **Full Item extraction** — splits all Parts (I / II / III / IV) and labels each Item as `extracted`, `incorporated_by_reference`, `not_applicable`, `reserved`, or `missing`
- **XBRL financial reconstruction** — parses Instance + Presentation + Label linkbases to rebuild Item 8 tables (Income Statement, Balance Sheet, Cash Flow, etc.)
- **Markdown rendering** — outputs clean, readable Markdown including numeric footnotes and text disclosures
- **Async job queue** — submit a filing and get a `job_id` immediately; poll for results when processing finishes
- **Caching** — same filing processed only once, keyed by `accession_number`
- **Dual input modes** — accepts `cik + accession_number` or a direct EDGAR URL
- **Admin panel** — job health dashboard, flag analytics, per-parser performance, and an item detail drawer

## Quick Start

**Prerequisites:** Python ≥ 3.10, Node.js ≥ 18

```bash
# Backend
cd api
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000  (interactive API docs at /docs)

# Frontend (new terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

**Environment variables**

`api/.env`
```
DB_PATH=./data/sec_extraction.db
CORS_ORIGINS=http://localhost:5173
```

`frontend/.env`
```
VITE_API_BASE_URL=http://localhost:8000
```

## Usage

Submit any filing via the web UI, or call the API directly:

```bash
# Submit a parsing job
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"cik":"0000320193","accession_number":"0000320193-23-000106"}'
# → { "job_id": "...", "status": "pending", "cache_hit": false }
```

Or use the parsing module directly in Python:

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

Full API reference: [docs/api.md](docs/api.md)

## Tech Stack

**Backend:** FastAPI · SQLite (aiosqlite) · lxml / BeautifulSoup · Pydantic · asyncio

**Frontend:** Vue 3 · TypeScript · Vite · Pinia · shadcn-vue · Tailwind CSS v4

## Project Layout

```
api/                  # FastAPI backend + parsing pipeline
├── sec_10k_pipeline/ # Core engine (regex, LLM-assisted, XBRL parsing)
└── ...
frontend/             # Vue 3 SPA
docs/                 # API reference, architecture notes, validator rules
```

## Contributing

Issues and pull requests are welcome. If you find a filing that parses incorrectly, or a feature you'd like to see, opening an issue is the best place to start — edge cases from real filings are especially useful.

1. Fork the repo and create a branch
2. Make your change with a clear commit message
3. Open a PR describing what changed and why

## License

MIT — see [LICENSE](LICENSE) for details.
