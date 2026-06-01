# Validator 規則說明

對應實作：[`api/sec_10k_pipeline/validators.py`](../api/sec_10k_pipeline/validators.py)

驗證層獨立於 parser，在 `postprocess` 之後執行，重新核對結構不變量,捕捉「parser 說成功、實際卻錯」的靜默錯誤,輸出 `QualityReport` 掛在 `FilingOutput.quality`。

- **輸入**：`raw_items`（parser 原始幾何 + spans + confidence）、最終 `items`（status 分類）、`text`（`doc.text` 全文）、`metadata`、`parse_result`
- **嚴重度**：`error`（幾乎確定是 bug）/ `warning`（可疑待人複查）/ `info`（提示）
- 多數門檻已用 `eval_datasets` 的人工標註語料校準,出處見文末「數據出處」與各規則標註。

---

## 規則總表

| Rule | flag code | 嚴重度 | 對象 | 一句話 |
|---|---|---|---|---|
| 0 | `range_invalid` | error | raw_items | 字元範圍須 `0 ≤ start < end ≤ len(text)` |
| 2 | `ordering_violation` | warning（多 span 路徑降 info） | raw_items | item 物理位置須照編號順序遞增 |
| 3′ | `oversized_item` | warning | raw_items | 單一 item 不該佔全體可讀內容過大比例 |
| 4 | `required_item_missing` / `recommended_item_missing` / `unexpected_item_status` | error / warning | items | 每個 item 的 status 須落在「正常」集合 |
| 4b | `item8_undersized` | warning | items | Item 8 標 extracted 卻過短（疑似漏抓的 by_reference） |
| 4c | `item1a_undersized` | warning | items | Item 1A 過短（門檻分 SRC / 非SRC） |
| 5 | `status_field_contract` | error | items | status 與 content/range 欄位須自洽 |
| 6 | `extracted_empty` | error | items | extracted 卻幾乎沒有可讀內容 |
| 7 | `document_too_short` / `document_short` | error / warning | text | 全文可讀長度過短 |
| 8 | `low_confidence_parse` / `low_confidence_item` | info | raw_items + parse_result | parser 信心低於門檻 |

> 「可讀字數」= 去除 HTML 標籤與 `[[ANCHOR]]`/`[[PAGE]]` 注入標記後的字元數（`_readable_length`），避免表格與標記灌水。

---

## 逐規則細節

### Rule 0 — `range_invalid`（error）
對每個 raw item 的每段 span 檢查 `0 ≤ start < end ≤ len(text)`。抓「標題定位錯誤」「座標被夾成 0」「反向 range」等幾何 bug。

### Rule 2 — `ordering_violation`（warning / info）
把有幾何的 item 按標準編號順序排，檢查 first-span 起始位置是否單調遞增；出現倒退即 flag。
- **多 span 路徑放寬**：當任一 raw item 帶 `spans`（cross-reference / pdf-style parser）時降為 `info`，因為這類年報的 SEC item 物理順序可能合法地不照編號。

### Rule 3′ — `oversized_item`（warning）
單一 item 的可讀字數佔「全體 item 可讀總和」比例 `> 45%`（`OVERSIZED_RATIO`）且絕對值 `> 50,000` 字（`OVERSIZED_MIN_READABLE`），視為疑似吞併了漏抓的鄰近 item。
- 僅在有幾何的 item ≥ 6（`OVERSIZED_MIN_ITEMS`）時才檢查。
- **排除天生大的 item** `{1, 1A, 7, 8}`（`NATURALLY_LARGE_ITEMS`）。〔出處：① 剖面,這四項 median ≥ 40k〕
- 同時計算 `coverage_ratio`（覆蓋率，僅作為報告指標,非 flag）。

### Rule 4 — per-item status 是否符合預期
依 `ITEM_EXPECTED_STATUS`（見下節）檢查每個 item 的 status：
- status ∈ 預期集合 → 不報。
- status ∉ 預期，且 item 屬 `CORE_ITEMS` → `required_item_missing`（**error**）。
- 例外：`1A` 且為 SRC（smaller reporting company）→ 降為 `recommended_item_missing`（**warning**）,因法規上 SRC 可省略 1A。
- status ∉ 預期,非核心 item → `unexpected_item_status`（**warning**),主要抓 Part III（10–14）`missing` 這類異常。

〔出處：① 剖面的「item 原型」;核心清單見下〕

### Rule 4b — `item8_undersized`（warning）
Item 8 標 `extracted` 但可讀字數 `< 40,000`（`ITEM8_MIN_EXTRACTED_READABLE`）→ 疑似「財報見 F-pages」的指標文字沒被識別成 `incorporated_by_reference`。
〔出處：① 剖面,清理後 Item 8 extracted 的 p5 ≈ 74k〕

### Rule 4c — `item1a_undersized`（warning）
Item 1A 標 `extracted` 但可讀字數低於下限 → 疑似被截斷或漏抓。**唯一分規模的長度門檻**：
- 非SRC：`< 25,000`（`ITEM1A_MIN_NON_SRC`）
- SRC：`< 20,000`（`ITEM1A_MIN_SRC`）

〔出處：② 規模分層,1A 是唯一明顯隨規模放大的 item（非SRC median 70k vs SRC 41k,1.73×）;門檻設在各桶觀測最小值（非SRC≈27.5k、SRC≈30k）之下避免誤判〕

### Rule 5 — `status_field_contract`（error）
status 與欄位須自洽：
- `extracted` → 必須有 content_text 且有 char_range。
- `reserved` / `not_applicable` / `missing` → 必須 content_text 與 char_range 皆為 null。
- `incorporated_by_reference` → 契約寬鬆,不檢查。

### Rule 6 — `extracted_empty`（error）
status=`extracted` 但可讀字數 `< 50`（`EXTRACTED_MIN_READABLE`）→ 內容幾乎為空,矛盾。

### Rule 7 — 文件長度地板
全文可讀字數：
- `< 30,000`（`DOC_FLOOR_ERROR`）→ `document_too_short`（**error**）,很可能抓錯主文件或 preprocess 清掉內容。
- `< 80,000`（`DOC_FLOOR_WARN`）→ `document_short`（**warning**）。

〔出處：①/③ 語料中最小的全文可讀長度 > 100k,故 30k/80k 為安全低標〕

### Rule 8 — 低信心（info）
- `parse_result.confidence < 0.7`（`CONFIDENCE_THRESHOLD`）→ `low_confidence_parse`。
- 任一 raw item `confidence < 0.7` → `low_confidence_item`。

---

## `ITEM_EXPECTED_STATUS`：每個 item 的「正常」status 集合

來源為 ① 逐 Item 剖面的觀察值。status 不在集合內即觸發 Rule 4。

| Item | 標題 | 正常 status | 備註 |
|---|---|---|---|
| 1 | Business | extracted | 核心 |
| 1A | Risk Factors | extracted | 核心（SRC 缺失降 warning） |
| 1B | Unresolved Staff Comments | not_applicable, extracted | 多為 N/A |
| 1C | Cybersecurity | extracted, not_applicable, missing | 2023+ 新規,過渡期容許 missing |
| 2 | Properties | extracted | 核心 |
| 3 | Legal Proceedings | extracted, not_applicable | 核心,但允許 N/A（無訴訟） |
| 4 | Mine Safety | not_applicable, extracted, missing | 多為 N/A |
| 5 | Market for Common Equity | extracted | 核心 |
| 6 | Reserved | reserved, extracted, not_applicable, missing | 2021+ 多為 reserved |
| 7 | MD&A | extracted | 核心 |
| 7A | Market Risk | extracted, not_applicable | SRC 常為 N/A |
| 8 | Financial Statements | extracted, incorporated_by_reference | 核心,允許 by_reference |
| 9 | Changes in Accountants | not_applicable, extracted, missing | 多為 N/A |
| 9A | Controls and Procedures | extracted | 核心 |
| 9B | Other Information | not_applicable, extracted | — |
| 9C | Foreign Jurisdictions | not_applicable, missing, extracted | 2021+ 新增,早年容許 missing |
| 10–14 | Part III | incorporated_by_reference, extracted | 多引用 proxy,missing 屬異常 |
| 15 | Exhibits | extracted | 核心 |
| 16 | Form 10-K Summary | not_applicable, extracted | 選填,多為 N/A |

**核心 item**（`CORE_ITEMS`,status 異常 → error）：`1, 1A, 2, 3, 5, 7, 8, 9A, 15`

---

## 輸出：`QualityReport`

掛在 `FilingOutput.quality`,並把每個 item 的 `confidence` 與命中的 `flag_codes` 回填到 `ItemResult`。

| 欄位 | 說明 |
|---|---|
| `is_valid` | 沒有任何 error → true |
| `score` | `max(0, 1 − 0.2 × error 數 − 0.05 × warning 數)` |
| `parser_name` / `parser_confidence` | 來自 parse_result |
| `expected_item_count` / `found_item_count` | 總 item 數 / status 為 extracted 或 by_reference 的數量 |
| `missing_items` | status=missing 的 item 清單 |
| `missing_required_items` | 觸發 `required_item_missing` / `recommended_item_missing` 的 item |
| `coverage_ratio` | raw span 覆蓋率（多 span 路徑才有意義） |
| `counts` | `{error, warning, info}` 各數量 |
| `flags` | 完整 `ValidationFlag` 清單（code / severity / item_number / message / detail） |

`info` 不影響 `score` 與 `is_valid`,只作提示。

---

## 數據出處

門檻校準來自 `eval_datasets` 的 34 份人工標註 10-K（見 [`eval_datasets/analysis/README.md`](../eval_datasets/analysis/README.md)）：

| 規則 / 常數 | 數據出處 |
|---|---|
| `ITEM_EXPECTED_STATUS` / `CORE_ITEMS` | ① 逐 Item 剖面（item 原型、100% extracted 的核心清單） |
| `NATURALLY_LARGE_ITEMS` = {1,1A,7,8} | ① 剖面 median ≥ 40k |
| `ITEM8_MIN_EXTRACTED_READABLE` = 40k | ① Item 8 extracted 的 p5 ≈ 74k |
| `ITEM1A_MIN_NON_SRC` / `_SRC` = 25k / 20k | ② 規模分層（1A 1.73×;各桶最小值 ≈27.5k/30k） |
| `DOC_FLOOR_ERROR/WARN` = 30k / 80k | ①/③ 最小全文可讀長度 > 100k |
| 1C / 9C 容許 `missing` | ③ 時間切面（1C 2023 過渡期 2/9 缺漏;9C pre-2021 尚未存在） |

**校準驗證**：34 份正常 GT 全跑,status / 長度類規則僅 2 個 flag,皆為真實邊緣案例,零誤報。

> 數據限制：語料 34 份、12 家公司、產業偏科技/零售,金融僅 1 檔。低頻 item 與細分桶的數值僅供參考,門檻多設為保守低標 + warning。
