import type { ValidationSeverity } from '@/types/api'

// flag code → 中文標籤（對應 api/sec_10k_pipeline/validators.py）
const FLAG_LABELS: Record<string, string> = {
  range_invalid: 'Range 不合法',
  ordering_violation: 'Item 順序異常',
  oversized_item: 'Item 過大',
  required_item_missing: '核心 Item 缺失',
  recommended_item_missing: '建議 Item 缺失',
  status_field_contract: 'Status 欄位矛盾',
  extracted_empty: '內容近乎空',
  document_too_short: '全文過短',
  document_short: '全文偏短',
  low_confidence_parse: '整份信心偏低',
  low_confidence_item: 'Item 信心偏低',
}

export function flagLabel(code: string): string {
  return FLAG_LABELS[code] ?? code
}

// severity → Badge variant
export function severityVariant(
  severity: ValidationSeverity,
): 'destructive' | 'warning' | 'info' {
  if (severity === 'error') return 'destructive'
  if (severity === 'warning') return 'warning'
  return 'info'
}

export function severityClasses(severity: ValidationSeverity): string {
  switch (severity) {
    case 'error':
      return 'bg-destructive/10 text-destructive border border-destructive/20'
    case 'warning':
      return 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20'
    default:
      return 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border border-blue-500/20'
  }
}

// 0..1 分數 → 顏色
export function scoreColor(score: number | null): string {
  if (score == null) return 'text-muted-foreground'
  if (score >= 0.9) return 'text-emerald-600 dark:text-emerald-500'
  if (score >= 0.7) return 'text-amber-600 dark:text-amber-500'
  return 'text-destructive'
}
