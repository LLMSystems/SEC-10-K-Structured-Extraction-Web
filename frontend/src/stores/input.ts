import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { JobSubmitInput } from '@/types/api'

export type InputMode = 'cik' | 'url'

export interface ExamplePreset {
  label: string
  cik: string
  accessionNumber: string
}

export const EXAMPLES: ExamplePreset[] = [
  { label: 'Apple 2023', cik: '0000320193', accessionNumber: '0000320193-23-000106' },
  { label: 'Microsoft 2024', cik: '0000789019', accessionNumber: '0000950170-24-087843' },
  { label: 'Tesla 2023', cik: '0001318605', accessionNumber: '0001628280-24-002390' },
]

export interface ValidationResult {
  ok: boolean
  message: string | null
  payload: JobSubmitInput | null
}

const CIK_RE = /^\d{1,10}$/
const ACC_RE = /^\d{10}-\d{2}-\d{6}$/

export const useInputStore = defineStore('input', () => {
  const mode = ref<InputMode>('cik')
  const cik = ref('')
  const accessionNumber = ref('')
  const url = ref('')

  function setMode(next: InputMode) {
    mode.value = next
  }

  function fillExample(preset: ExamplePreset) {
    mode.value = 'cik'
    cik.value = preset.cik
    accessionNumber.value = preset.accessionNumber
  }

  function reset() {
    cik.value = ''
    accessionNumber.value = ''
    url.value = ''
  }

  const validation = computed<ValidationResult>(() => {
    if (mode.value === 'cik') {
      const c = cik.value.trim()
      const a = accessionNumber.value.trim()
      if (!c || !a) {
        return { ok: false, message: '請同時輸入 CIK 與 Accession Number。', payload: null }
      }
      if (!CIK_RE.test(c)) {
        return { ok: false, message: 'CIK 須為最多 10 位的數字。', payload: null }
      }
      if (!ACC_RE.test(a)) {
        return {
          ok: false,
          message: 'Accession Number 格式須為 0000000000-00-000000。',
          payload: null,
        }
      }
      return { ok: true, message: null, payload: { cik: c, accession_number: a } }
    }
    const u = url.value.trim()
    if (!u) return { ok: false, message: '請輸入 URL。', payload: null }
    if (!/^https?:\/\//i.test(u)) {
      return { ok: false, message: 'URL 須以 http(s):// 開頭。', payload: null }
    }
    return { ok: true, message: null, payload: { url: u } }
  })

  return {
    mode,
    cik,
    accessionNumber,
    url,
    validation,
    setMode,
    fillExample,
    reset,
  }
})
