import type {
  AdminStats,
  FilingFilter,
  FilingListResponse,
  FilingOutput,
  FilingSort,
  FlagAnalytics,
  JobAnalytics,
  JobResponse,
  JobSubmitInput,
  JobSubmitResponse,
} from '@/types/api'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  detail: unknown
  constructor(status: number, message: string, detail?: unknown) {
    super(message)
    this.status = status
    this.detail = detail
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!resp.ok) {
    let detail: unknown = null
    let message = `Request failed with status ${resp.status}`
    try {
      detail = await resp.json()
      if (detail && typeof detail === 'object' && 'detail' in detail) {
        const d = (detail as { detail: unknown }).detail
        if (typeof d === 'string') message = d
      }
    } catch {
      // ignore
    }
    throw new ApiError(resp.status, message, detail)
  }
  return resp.json() as Promise<T>
}

export const api = {
  submitJob(input: JobSubmitInput): Promise<JobSubmitResponse> {
    return request<JobSubmitResponse>('/jobs', {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },
  getJob(jobId: string): Promise<JobResponse> {
    return request<JobResponse>(`/jobs/${jobId}`)
  },
  getFiling(accessionNumber: string): Promise<FilingOutput> {
    return request<FilingOutput>(`/filings/${accessionNumber}`)
  },
  // ── Admin / Dashboard ──
  adminStats(): Promise<AdminStats> {
    return request<AdminStats>('/admin/stats')
  },
  adminFilings(params: {
    sort?: FilingSort
    only?: FilingFilter
    limit?: number
    offset?: number
  } = {}): Promise<FilingListResponse> {
    const qs = new URLSearchParams()
    if (params.sort) qs.set('sort', params.sort)
    if (params.only) qs.set('only', params.only)
    if (params.limit != null) qs.set('limit', String(params.limit))
    if (params.offset != null) qs.set('offset', String(params.offset))
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return request<FilingListResponse>(`/admin/filings${suffix}`)
  },
  adminFlagStats(): Promise<FlagAnalytics> {
    return request<FlagAnalytics>('/admin/flag-stats')
  },
  adminJobStats(): Promise<JobAnalytics> {
    return request<JobAnalytics>('/admin/job-stats')
  },
  // POST /xbrl-markdown — synchronous, 5–15s, returns text/markdown
  async xbrlMarkdown(cik: string, accession_number: string): Promise<string> {
    const resp = await fetch(`${BASE_URL}/xbrl-markdown`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cik, accession_number }),
    })
    if (!resp.ok) {
      let message = `Request failed with status ${resp.status}`
      try {
        const data = (await resp.json()) as { detail?: unknown }
        if (typeof data.detail === 'string') message = data.detail
        else if (data.detail) message = JSON.stringify(data.detail)
      } catch {
        // ignore non-JSON error bodies
      }
      throw new ApiError(resp.status, message)
    }
    return resp.text()
  },
}
