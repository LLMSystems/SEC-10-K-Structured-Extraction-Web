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
}

export interface FilingTiming {
  fetch_html_sec: number
  preprocess_sec: number
  parse_sec: number
  postprocess_sec: number
}

export interface FilingOutput {
  filing_info: FilingInfo
  items: FilingItem[]
  timing: FilingTiming
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
