export type ItemStatus =
  | 'extracted'
  | 'incorporated_by_reference'
  | 'not_applicable'
  | 'reserved'
  | 'missing'

export interface FilingInfo {
  cik: string
  accession_number: string
  company_name: string | null
  fiscal_year_end: string | null
  filer_category: string | null
}

export interface FilingItem {
  part: string
  item_number: string
  item_title: string
  content_text: string | null
  char_range: [number, number] | null
  status: ItemStatus
  confidence: number | null
  flag_codes: string[]
}

export interface FilingTiming {
  fetch_html_sec: number
  preprocess_sec: number
  parse_sec: number
  postprocess_sec: number
}

export type ValidationSeverity = 'error' | 'warning' | 'info'

export interface ValidationFlag {
  code: string
  severity: ValidationSeverity
  item_number: string | null
  message: string
  detail: Record<string, unknown>
}

export interface QualityReport {
  is_valid: boolean
  score: number
  parser_name: string
  parser_confidence: number
  expected_item_count: number
  found_item_count: number
  missing_items: string[]
  missing_required_items: string[]
  coverage_ratio: number
  counts: Record<string, number>
  flags: ValidationFlag[]
}

export interface FilingOutput {
  filing_info: FilingInfo
  items: FilingItem[]
  timing: FilingTiming
  quality: QualityReport | null
}

// ── Admin / Dashboard ──────────────────────────────────────

export interface AdminStats {
  total_filings: number
  valid_count: number
  invalid_count: number
  avg_score: number | null
  error_filings: number
  warning_filings: number
  avg_processing_ms: number | null
  failed_jobs: number
}

export interface FilingListItem {
  accession_number: string
  company_name: string | null
  fiscal_year_end: string | null
  parser_name: string | null
  quality_score: number | null
  quality_valid: boolean | null
  quality_errors: number | null
  quality_warnings: number | null
  processing_ms: number | null
  fetched_at: string
}

export interface FilingListResponse {
  total: number
  items: FilingListItem[]
}

export type FilingSort = 'score_asc' | 'score_desc' | 'recent'
export type FilingFilter = 'all' | 'errors' | 'invalid'

// ── 規則分析 ④ ──
export interface FlagCount {
  code: string
  severity: ValidationSeverity
  count: number
}

export interface ItemFlagCount {
  item_number: string
  count: number
}

export interface ParserStat {
  parser_name: string | null
  filings: number
  errors: number
  warnings: number
  avg_score: number | null
}

export interface FlagAnalytics {
  by_code: FlagCount[]
  by_item: ItemFlagCount[]
  by_parser: ParserStat[]
  timing: FilingTiming | null
  total_flags: number
}

// ── 系統健康 ⑤ ──
export interface JobSummary {
  job_id: string
  status: JobStatus
  accession_number: string | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface JobAnalytics {
  status_counts: Record<string, number>
  recent_failures: JobSummary[]
}

export type JobStatus = 'pending' | 'running' | 'done' | 'failed'

export interface JobSubmitCikInput {
  cik: string
  accession_number: string
}

export interface JobSubmitUrlInput {
  url: string
}

export type JobSubmitInput = JobSubmitCikInput | JobSubmitUrlInput

export interface JobSubmitResponse {
  job_id: string
  status: JobStatus
  cache_hit: boolean
}

export interface JobResponse {
  job_id: string
  status: JobStatus
  result: FilingOutput | null
  error: string | null
  created_at: string
  completed_at: string | null
}
