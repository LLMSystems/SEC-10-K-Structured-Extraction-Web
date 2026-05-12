import type {
  FilingOutput,
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
}
