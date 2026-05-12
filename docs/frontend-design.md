# SEC 10-K Structured Extraction Web Demo — 前端設計構想文檔

---

## 一、設計方向與視覺風格

### 核心：Zinc

**概念**：以 shadcn/ui Zinc 主題為基底，用中性灰構建乾淨、無干擾的閱讀環境。大量留白、精準的字型層級、低調的邊框，讓結構化的 10-K 資料成為畫面主角。品牌藍僅用於關鍵互動（CTA、active state、連結）。

**Light / Dark 雙模式**，預設 Light，使用者可手動切換，偏好記憶在 `localStorage`。

**色調系統（使用 shadcn-vue Zinc 主題語義 token）**

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `--background` | `zinc-50` `#fafafa` | `zinc-950` `#09090b` | 頁面底色 |
| `--card` | `white` `#ffffff` | `zinc-900` `#18181b` | 卡片、側欄底色 |
| `--border` | `zinc-200` `#e4e4e7` | `zinc-800` `#27272a` | 分隔線、輸入框邊框 |
| `--foreground` | `zinc-900` `#18181b` | `zinc-50` `#fafafa` | 主文字 |
| `--muted-foreground` | `zinc-500` `#71717a` | `zinc-400` `#a1a1aa` | 次要標籤、說明文字 |
| `--primary` | `blue-600` `#2563eb` | `blue-500` `#3b82f6` | CTA 按鈕、active item、連結 |
| `--primary-foreground` | `white` | `white` | primary 按鈕內文字 |
| `--destructive` | `red-500` `#ef4444` | `red-500` | 錯誤狀態 |
| 成功色（自訂） | `emerald-600` `#059669` | `emerald-500` | extracted 狀態圖示 |
| 警告色（自訂） | `amber-500` `#f59e0b` | `amber-400` | missing 狀態圖示 |

**字型配對**

| 用途 | 字型 | 說明 |
|------|------|------|
| 全站介面 / 標籤 / 導航 | `Geist Sans` | 現代無襯線，shadcn 預設搭配，清晰可讀 |
| 數字 / ID / Accession Number | `Geist Mono` | 等寬，讓 ID 對齊、易讀 |
| Item 長文內容 | `system-ui` fallback | 不額外載入字型，減少長文閱讀負擔 |

**氛圍細節**

- 卡片使用 `shadow-sm`（Light）/ 無陰影 + `border`（Dark），不用誇張投影
- Active item 左側用 `border-l-2 border-primary` 標示，背景 `bg-primary/5`，不用色塊填滿
- 按鈕 hover 使用 `bg-primary/90`，輕微縮放 `scale-[0.98]`，動作克制
- 頁面轉場：`opacity-0 → opacity-100` + `translate-y-2 → translate-y-0`，100ms，不過度花俏
- 輸入框 focus：`ring-2 ring-primary/30`，藍色暈圈取代預設黑色 outline

---

## 二、框架與技術棧要求

### 核心框架

| 技術 | 版本 | 用途 |
|------|------|------|
| Vue 3 | `^3.5` | Composition API + `<script setup>` 語法，全面使用 `ref` / `computed` / `defineProps` |
| Vue Router | `^5.0` | SPA 路由管理，History 模式 |
| Pinia | `^3.0` | 狀態管理，取代 Vuex |
| TypeScript | `~6.0` | 全程強型別，Props / Store / API response 均需定義 interface |
| Vite | `^8.0` | 開發伺服器與打包 |

### UI 元件：shadcn-vue + Tailwind CSS v4

**shadcn-vue** 採用「複製到專案」的元件模式，所有元件原始碼放在 `src/components/ui/`，可自由客製化。

**必須使用 shadcn-vue 的元件清單：**

| shadcn-vue 元件 | 用於 |
|----------------|------|
| `Button` | CTA 按鈕、快捷範例、操作按鈕 |
| `Input` | CIK、Accession Number、URL 輸入欄 |
| `Tabs` / `TabsList` / `TabsTrigger` | CIK 模式 / URL 模式切換 |
| `Card` / `CardHeader` / `CardContent` | 輸入卡片、公司資訊卡 |
| `Badge` | Item status 標籤 |
| `Separator` | 分隔線 |
| `Skeleton` | 深連結訪問時的載入骨架屏 |
| `Toast` / `Toaster` | cache hit 提示、錯誤通知 |
| `ScrollArea` | Item 導覽列、內文區的自訂捲軸樣式 |
| `Tooltip` | status 圖示的說明提示 |

**Tailwind CSS v4 使用規範：**

- 使用 CSS-first 設定（`@theme` 取代 `tailwind.config.js`），在 `src/assets/main.css` 統一定義 design token
- 直接沿用 shadcn-vue Zinc 主題的 CSS 變數命名慣例（`--background`、`--foreground`、`--primary`...），Light / Dark 透過 `.dark` class 切換

```css
/* src/assets/main.css */
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-border: var(--border);
  --color-muted-foreground: var(--muted-foreground);

  --font-sans: "Geist Sans", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "Geist Mono", ui-monospace, monospace;
}

/* Light mode — Zinc */
:root {
  --background: #fafafa;           /* zinc-50 */
  --card: #ffffff;
  --foreground: #18181b;           /* zinc-900 */
  --muted-foreground: #71717a;     /* zinc-500 */
  --border: #e4e4e7;               /* zinc-200 */
  --input: #e4e4e7;
  --primary: #2563eb;              /* blue-600 */
  --primary-foreground: #ffffff;
  --destructive: #ef4444;          /* red-500 */
  --success: #059669;              /* emerald-600 */
  --warning: #f59e0b;              /* amber-500 */
  --radius: 0.5rem;
}

/* Dark mode — Zinc */
.dark {
  --background: #09090b;           /* zinc-950 */
  --card: #18181b;                 /* zinc-900 */
  --foreground: #fafafa;           /* zinc-50 */
  --muted-foreground: #a1a1aa;     /* zinc-400 */
  --border: #27272a;               /* zinc-800 */
  --input: #27272a;
  --primary: #3b82f6;              /* blue-500 */
  --primary-foreground: #ffffff;
  --destructive: #ef4444;
  --success: #10b981;              /* emerald-500 */
  --warning: #fbbf24;              /* amber-400 */
}
```

- 元件內只使用 Tailwind utility class，**禁止**寫 scoped CSS（除非處理第三方元件無法用 class 覆蓋的情況）
- 動畫優先使用 `tw-animate-css` 套件提供的 utility，複雜動畫才用 `@keyframes`

### 圖示：Lucide Vue Next

全站圖示統一使用 `lucide-vue-next`，按需引入單一元件，避免打包整包：

```typescript
import { CheckCircle, ExternalLink, AlertCircle, Minus, ArrowLeft } from 'lucide-vue-next'
```

### 專案結構

```
frontend/src/
├── assets/
│   └── main.css              Tailwind v4 @theme 定義
├── components/
│   ├── ui/                   shadcn-vue 元件（勿手動編輯）
│   ├── layout/               AppHeader、AppToast
│   ├── home/                 首頁相關元件
│   ├── result/               結果頁相關元件
│   └── common/               通用元件
├── stores/                   Pinia stores
├── router/
│   └── index.ts              路由定義
├── types/
│   └── api.ts                API request / response interface
├── lib/
│   ├── api.ts                fetch 封裝（POST /jobs、GET /jobs/{id}）
│   └── utils.ts              shadcn-vue 的 cn() helper
└── views/
    ├── HomeView.vue
    └── ResultView.vue
```

---

## 三、頁面與路由結構


```
/ (根路由)
├── / → <HomePage>          輸入表單，單頁核心
└── /result/:jobId → <ResultPage>   結果瀏覽器（可深連結分享）

全域：
├── <AppHeader>             固定頂部導航
└── <AppToast>              通知系統（cache hit、錯誤提示）
```

**刻意保持 SPA 簡潔**：兩個路由，避免過度設計。`/result/:jobId` 支援直接貼 URL 分享結果，背後重新查詢 API。

---

## 四、各頁面 Wireframe 描述

### 4.1 首頁 `<HomePage>` — 輸入與提交

```
┌──────────────────────────────────────────────────────────────┐
│ [LOGO] SEC 10-K Extractor        [GitHub ↗]                  │  ← AppHeader (h-14, sticky)
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                     │  ← 背景：橫向掃描線 + 極暗漸層
│                                                              │
│         ┌────────────────────────────────────────┐           │
│         │  DM Serif Display, 36px                │           │
│         │  Extract SEC 10-K Filings              │           │
│         │  Structured in Seconds.                │           │
│         │                                        │           │
│         │  ┌──────────────────────────────────┐  │           │  ← 輸入卡片，深色背景 + 琥珀邊框頂部
│         │  │  [CIK + 申報編號] [URL] ← Tab切換│  │           │
│         │  │  ─────────────────────────────── │  │           │
│         │  │                                  │  │           │
│         │  │  [Tab: CIK 模式]                 │  │           │
│         │  │  CIK:                            │  │           │
│         │  │  ┌────────────────────────────┐  │  │           │
│         │  │  │ 0000320193                 │  │  │           │
│         │  │  └────────────────────────────┘  │  │           │
│         │  │  Accession Number:               │  │           │
│         │  │  ┌────────────────────────────┐  │  │           │
│         │  │  │ 0000320193-23-000106       │  │  │           │
│         │  │  └────────────────────────────┘  │  │           │
│         │  │                                  │  │           │
│         │  │  [Tab: URL 模式]（隱藏）         │  │           │
│         │  │  SEC EDGAR URL:                  │  │           │
│         │  │  ┌────────────────────────────┐  │  │           │
│         │  │  │ https://www.sec.gov/...    │  │  │           │
│         │  │  └────────────────────────────┘  │  │           │
│         │  │                                  │  │           │
│         │  │  ┌──────────────────────────────┐│  │           │
│         │  │  │  ▶  Extract Filing            ││  │           │  ← 琥珀金 CTA 按鈕
│         │  │  └──────────────────────────────┘│  │           │
│         │  └──────────────────────────────────┘  │           │
│         │                                        │           │
│         │  快捷範例：                             │           │  ← 點擊自動填入
│         │  [Apple 2023] [Microsoft 2024] [Tesla 2023]         │
│         └────────────────────────────────────────┘           │
│                                                              │
│   ─────────────────── HOW IT WORKS ───────────────────       │  ← 頁面下方說明區塊（3 步驟）
│   [1. 輸入] → [2. 非同步解析 ~0.7s] → [3. 結構化輸出]       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**提交後：原地展示進度條**

```
│  [✓] Job 已送出  job_id: 3fa85f64...
│
│  ████████████░░░░░░░░░  running...
│  Fetching HTML → Preprocessing → Parsing → Done
│      [0.16s]        [0.49s]        [0.04s]
│
│  ─── 或 cache hit 時 ───
│  ⚡ 快取命中！此文件已於先前處理過。
```

進度條完成後自動跳轉至 `/result/:jobId`。

---

### 4.2 結果頁 `<ResultPage>` — 三欄式閱讀器

```
┌──────────────────────────────────────────────────────────────────────┐
│ [←] SEC 10-K Extractor   Apple Inc. · FY2023              [分享] [↓] │  ← AppHeader，帶公司名與操作按鈕
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ ┌──────────────┐ ┌─────────────────────────┐ ┌──────────────────┐   │
│ │              │ │                         │ │                  │   │
│ │  公司資訊卡  │ │   Item 導覽列（左側欄）  │ │  Item 內文區     │   │
│ │  ──────────  │ │                         │ │  （主內容）      │   │
│ │  Apple Inc.  │ │  Part I                 │ │                  │   │
│ │  CIK: 0000.. │ │  ├─ Item 1  Business ✓  │ │  Item 1. Business│   │
│ │  FY: 2023-09 │ │  ├─ Item 1A Risk... ✓   │ │  ─────────────── │   │
│ │  Large Accel │ │  ├─ Item 1B Unsett. ✓   │ │  Apple Inc. desig│   │
│ │              │ │  ├─ Item 2  Prop... ✓   │ │  ns, manufactures│   │
│ │  ──────────  │ │  └─ Item 3  Legal.. ✓   │ │  and markets smar│   │
│ │  處理時間    │ │                         │ │  tphones...      │   │
│ │  Total: 0.7s │ │  Part II                │ │                  │   │
│ │  ──────────  │ │  ├─ Item 5  Market ✓    │ │  （長文捲動）    │   │
│ │  ▓▓░░░░ 0.16 │ │  ├─ Item 6  ╌╌╌╌╌ ═    │ │                  │   │
│ │  ▓▓▓▓▓░ 0.49 │ │  ├─ Item 7  MD&A.. ✓   │ │                  │   │
│ │  ▓░░░░░ 0.04 │ │  └─ Item 9  Changes ✓  │ │                  │   │
│ │              │ │                         │ │                  │   │
│ │              │ │  Part III               │ │                  │   │
│ │              │ │  ├─ Item 10 Director ↗  │ │                  │   │
│ │              │ │  └─ Item 11 Exec. C. ↗  │ │                  │   │
│ │              │ │                         │ │                  │   │
│ │              │ │  Part IV                │ │                  │   │
│ │              │ │  └─ Item 15 Exhibits ✓  │ │                  │   │
│ └──────────────┘ └─────────────────────────┘ └──────────────────┘   │
│  w-64 固定         w-56 固定，可捲動           flex-1，內容捲動      │
└──────────────────────────────────────────────────────────────────────┘
```

**Item 導覽列的 Status 圖示**

| Status | 圖示 | 顏色 | 說明 |
|--------|------|------|------|
| `extracted` | `✓` CheckCircle | 成功綠 | 正常抽取，有內文 |
| `incorporated_by_reference` | `↗` ExternalLink | 天藍 | 引用自其他文件 |
| `not_applicable` | `—` Minus | 灰 | 公司聲明不適用 |
| `reserved` | `═` (雙橫線) | 暗灰 | SEC 保留項目 |
| `missing` | `?` AlertCircle | 警告橘 | Parser 未找到 |

---

## 五、核心元件清單

```
src/components/
│
├── layout/
│   ├── AppHeader.vue          頂部導航，含 Logo、麵包屑、操作按鈕
│   └── AppToast.vue           通知氣泡（cache hit、錯誤）
│
├── home/
│   ├── ExtractionForm.vue     主要輸入卡片
│   ├── InputModeTabs.vue      CIK模式 / URL模式 切換 Tab
│   ├── CikInputGroup.vue      CIK + Accession Number 雙欄輸入
│   ├── UrlInputGroup.vue      SEC URL 單行輸入
│   ├── QuickExamples.vue      快捷範例按鈕列
│   └── JobProgressBar.vue     提交後的進度追蹤條（含 pipeline 步驟動畫）
│
├── result/
│   ├── FilingInfoCard.vue     左側欄：公司資訊 + 處理時間長條圖
│   ├── ItemNavigator.vue      中間欄：Item 導覽樹，帶 status 圖示
│   ├── ItemContent.vue        右側主區：Item 內文閱讀器
│   ├── ItemStatusBadge.vue    可複用的 status 標籤元件
│   ├── TimingChart.vue        4 階段處理時間視覺化長條
│   └── ShareButton.vue        複製結果深連結按鈕
│
└── common/
    ├── MonoText.vue           等寬文字包裝（用於 ID、數字）
    ├── ScanlineBackground.vue 背景掃描線紋理效果
    └── LoadingSpinner.vue     載入動畫
```

---

## 六、Pinia 狀態管理設計

### `useJobStore`（主要 Store）

```typescript
interface JobStore {
  // 狀態
  phase: 'idle' | 'submitting' | 'polling' | 'done' | 'error'
  jobId: string | null
  cacheHit: boolean
  currentJob: JobResponse | null      // GET /jobs/{id} 的回應
  filingResult: FilingOutput | null   // result 展開後的資料
  error: string | null
  pollingInterval: number | null

  // 動作
  submitJob(input: CikInput | UrlInput): Promise<void>
  startPolling(jobId: string): void
  stopPolling(): void
  loadJobById(jobId: string): Promise<void>  // 用於直接訪問 /result/:jobId
  reset(): void
}
```

### `useNavigatorStore`（結果頁導覽）

```typescript
interface NavigatorStore {
  activeItemIndex: number | null    // 目前選中的 item
  expandedParts: Set<string>        // 展開的 Part（Part I / II / III / IV）

  setActiveItem(index: number): void
  togglePart(part: string): void
}
```

### `useInputStore`（表單暫存）

```typescript
interface InputStore {
  mode: 'cik' | 'url'
  cik: string
  accessionNumber: string
  url: string

  setMode(mode: 'cik' | 'url'): void
  fillExample(preset: ExamplePreset): void
  validate(): ValidationResult
}
```

---

## 七、API 互動流程

### 提交與 Polling 流程

```
使用者點擊「Extract Filing」
        │
        ▼
[useJobStore.submitJob()]
   phase = 'submitting'
        │
        ▼
POST /jobs
        │
   ┌────┴────┐
cache_hit?   否
   是        │
   │         ▼
   │   phase = 'polling'
   │   startPolling(jobId)
   │         │
   │    每 1 秒 GET /jobs/{id}
   │         │
   │    ┌────┴─────────────────┐
   │   done?  failed?   pending/running
   │    │       │              │
   │    │       │         繼續 polling
   │    │    phase='error'
   │    │    stopPolling()
   │    │
   ▼    ▼
phase = 'done'
filingResult = result
stopPolling()
router.push(`/result/${jobId}`)
```

### Polling 實作重點

```typescript
// 使用 setInterval，但限制最大次數防止無限等待
const MAX_POLLS = 60  // 最多等 60 秒

function startPolling(jobId: string) {
  let count = 0
  pollingInterval = setInterval(async () => {
    count++
    if (count > MAX_POLLS) {
      stopPolling()
      error = 'Timeout: 處理時間超過預期，請稍後再試'
      phase = 'error'
      return
    }
    const job = await api.getJob(jobId)
    currentJob = job
    if (job.status === 'done') {
      filingResult = job.result
      phase = 'done'
      stopPolling()
      router.push(`/result/${jobId}`)
    } else if (job.status === 'failed') {
      error = job.error
      phase = 'error'
      stopPolling()
    }
  }, 1000)
}
```

### Cache Hit 特殊動畫

當 `cache_hit = true`，跳過 polling，直接展示 **0.3 秒** 的「⚡ 快取命中」提示動畫，再導向結果頁，強調快取的速度優勢。

---

## 八、Item Status 視覺呈現細節

### 導覽列 Item 行

```
┌────────────────────────────────────────┐
│ ▌ Item 1   Business              [✓]   │  ← active: border-l-2 border-primary + bg-primary/5 + text-primary
│   Item 1A  Risk Factors          [✓]   │  ← 非 active: hover:bg-zinc-100 dark:hover:bg-zinc-800
│   Item 7   MD&A                  [✓]   │
│   Item 10  Directors             [↗]   │  ← 引用（text-blue-600，可點擊提示）
│   Item 6   Selected Fin. Data    [═]   │  ← 保留（text-zinc-400，cursor-default 不可選）
│   Item 4   Mine Safety           [—]   │  ← 不適用（text-zinc-400）
│   Item 99  Executive Comp.       [?]   │  ← 遺漏（text-amber-500，帶 Tooltip 說明）
└────────────────────────────────────────┘
```

**Status 圖示對照（Zinc 色系）**

| Status | 圖示元件 | Tailwind class | 說明 |
|--------|----------|---------------|------|
| `extracted` | `CheckCircle2` | `text-emerald-600` | 成功抽取 |
| `incorporated_by_reference` | `ExternalLink` | `text-blue-500` | 引用外部文件 |
| `not_applicable` | `Minus` | `text-zinc-400` | 公司聲明不適用 |
| `reserved` | `Ban` | `text-zinc-400` | SEC 保留項目 |
| `missing` | `AlertCircle` | `text-amber-500` | Parser 未找到 |

### 內文區各 Status 的呈現

| Status | 內文區呈現方式 |
|--------|---------------|
| `extracted` | 正常渲染 `content_text`，`text-foreground`，行距 1.8，`font-sans` |
| `incorporated_by_reference` | `bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800` 提示框：說明引用來源 + ExternalLink 圖示 |
| `not_applicable` | `text-muted-foreground italic` 斜體提示：「公司聲明此項目不適用」 |
| `reserved` | `bg-zinc-100 dark:bg-zinc-800` 灰色提示框：「SEC 規定保留項目（自 [年份] 起）」 |
| `missing` | `bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800` 警告框 + AlertCircle 圖示 |

---

## 九、互動細節與動畫規格

### 頁面轉場
- 首頁 → 結果頁：Vue Router `<Transition name="slide-up">`，內容區從 `translateY(24px)` 淡入
- 結果頁直接訪問（深連結）：顯示骨架屏 skeleton，等 API 回應完成後淡入

### JobProgressBar 動畫

```
階段指示燈：● ○ ○ ○   Fetching HTML...
            ● ● ○ ○   Preprocessing...
            ● ● ● ○   Parsing...
            ● ● ● ●   Done ✓

進度條：使用 CSS animation 推進，非真實後端進度，
        給予良好的感知體驗（Indeterminate → 完成時跳至 100%）
```

### Item 切換動畫
- 切換 Item 時，內文區 `opacity: 0 → 1` + `translateX(8px) → 0`，持續 150ms

---

## 十、響應式設計

| 斷點 | 布局調整 |
|------|---------|
| `> 1280px` | 完整三欄（公司卡 + 導覽 + 內文） |
| `768px–1280px` | 公司卡折疊進頂部橫條，保留兩欄（導覽 + 內文） |
| `< 768px` | 單欄，Item 導覽改為底部 Drawer 展開 |

---

## 十一、建議實作順序

```
Phase 1：核心功能
  [ ] 建立路由結構 + AppHeader
  [ ] ExtractionForm + InputModeTabs（僅 UI，不串接）
  [ ] useJobStore + API 層（axios/fetch 封裝）
  [ ] JobProgressBar + polling 邏輯

Phase 2：結果呈現
  [ ] FilingInfoCard + TimingChart
  [ ] ItemNavigator（帶 status 圖示）
  [ ] ItemContent（各 status 呈現）
  [ ] 深連結支援（/result/:jobId 直接訪問）
  [ ] AppToast（cache hit 提示）

Phase 3：細節打磨
  [ ] 動畫細節（轉場、掃描線背景、暈光效果）
  [ ] 響應式調整（Drawer 模式）
  [ ] 快捷範例 QuickExamples
  [ ] 錯誤狀態處理（failed job、404、timeout）
```
