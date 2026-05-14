# AI 協作開發說明

**使用工具 : Claude Code**

## 人與 AI 的協作模式

本次前後端開發採用「人工主導、AI 協作」+ skill 的方式進行開發。由我負責定義前後端架構、實現要求，主要是根據 [SEC-10-K-Structured-Extraction](https://github.com/LLMSystems/SEC-10-K-Structured-Extraction) 這個項目為核心開發前後端，我自己主要熟悉有經驗的前後端架構是 vue3 + fastapi，vue3 的好處是 Vue 3 + Vite 有提供模組化的開發體驗，而且原生 Fetch 與 Vue 內建狀態管理保持架構輕量，易維護與擴展。FastAPI 的話是因為異步、型別安全與自動 API 文件，所以以這個組合進行開發

再開發之前我自己準備兩個 skill，一個是 [shadcn-vue-tailwind-frontend](../prompt/skills/shadcn-vue-tailwind-frontend/SKILL.md)，主要是一份針對 Vue 3 + shadcn-vue + Tailwind CSS v4 技術棧的前端開發規範。另外一份是 [fastapi-job-api-backend](../prompt/skills/fastapi-job-api-backend/SKILL.md)，是 FastAPI 後端開發規範，定義如何建構接受請求、將長時任務排入背景執行佇列、以 SQLite 追蹤 Job 狀態

上面兩份 skill 都是根據我希望這個 web 該怎麼開發設計的 

這樣的協作模式讓我可以保有對專案方向與品質的決策權，同時利用 AI 加快整理、撰寫與分析的速度。

## 實際協作紀錄

本專案的協作過程可分為前端/後端需求規格文檔撰寫、規格收斂、協作開發與測試四個階段，並分別反映在既有文件中。

首先在前後端需求規格文檔撰寫階段，我先把需求拆成可以執行的模組，再讓 AI 協助整理成結構化文檔。後端部分以 API 輸入輸出、Job 生命週期、背景執行流程與資料表欄位為主，前端部分則先定義頁面結構、互動流程、狀態呈現與元件拆分。這個階段的重點不是直接產生大量程式碼，而是把「要做什麼」先說清楚，讓後續開發有一致標準。可看以下文檔 : [後端設計文檔](../docs/api-design.md)、[後端規格文檔](../docs/api.md)、[前端設計文檔](../docs/frontend-design.md)

接著在規格收斂階段，我會調整 AI 產出的文檔，針對實際實現的需求與文檔的差別進行調整

在協作開發階段，我會請 AI 使用 skill 依規格產出第一版後端路由與服務流程、前端頁面與元件骨架。實作上主要困難在可追蹤的 Job Queue、可輪詢的狀態 API 與 SQLite 寫入流程；前端也是一樣，請 AI 使用 skill 依規格產出第一版然後我自行測試


## Prompt 紀錄

### 後端

我在後端協作時，下 prompt 的方式通常是「先講我要的流程，再補限制條件」。

prompt 例如(通常會搭配 [fastapi-job-api-backend](../prompt/skills/fastapi-job-api-backend/SKILL.md) skill)：

- 幫我根據 [後端設計文檔](../docs/api-design.md) 先把 FastAPI 的 job API 骨架生出來，核心是 POST /jobs 送出後要立刻回 job_id，不要等長任務跑完
- 幫我把雙輸入模式補上，除了 cik + accession_number，也要支援直接丟 EDGAR URL(可以參考`./api/sec_10k_pipeline/pipeline.py`)
- 我現在要補 Item status，請把 extracted、incorporated_by_reference、not_applicable、reserved、missing 五種狀態都整理進輸出
- 幫我加一個 /xbrl-markdown，流程是先抓 Item 8 的 XBRL facts，區分主要報表與補充保表，並組成 md 檔 後直接回 markdown 文字(請先幫我網路搜索整理 xbrl api重點，整理後先跟我討論，確定規格後再進行初版開發)

這類 prompt 通常不是一次到位，我會先看 API 回傳，再追加「哪個欄位不夠」、「哪個狀態不準」、「哪裡要改成 cache 命中優先」去做第二輪、第三輪修正。

### 前端

我在前端協作時，prompt 會更偏「畫面行為 + 狀態切換」，讓 AI 先做可操作版本，再慢慢修細節。

prompt 例如(通常會搭配 [shadcn-vue-tailwind-frontend](../prompt/skills/shadcn-vue-tailwind-frontend/SKILL.md) skill)：

- 幫我調整三欄寬度限制，不要限制寬度，這樣調整網頁大小比例可以充滿，然後item內文顯示欄也幫我不要限制寬度


## AI 在本專案中的具體貢獻

AI 在本專案中的貢獻主要集中在以下幾個面向：

- 協助我整理前後端開發文檔，包含 api 端點開發協作與前端介面文檔開發

- 前端頁面基礎開發、後端骨架開發

## 我如何驗證 AI 產出&調整

為了避免直接採信 AI 產出的內容，我在本專案中採用了幾種驗證方式。

- 前端 : 確認畫面操作無誤、型別檢查、自行跑測試。
- 後端 : 初版開發完後確保型別定義正確，資料庫寫入正常、端口測試是否正常
- 對代碼進行人工複查，特別是 job queue 以及相同財報應該要 cache 命中使用。
- 針對 AI 產出的規範內容進行人工修訂，避免語意模糊、過度延伸或與實作脫節或是與我想法有出入，通常會充分與 AI 溝通。