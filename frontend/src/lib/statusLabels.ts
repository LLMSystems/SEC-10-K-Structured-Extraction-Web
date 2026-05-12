import type { ItemStatus } from '@/types/api'

const LABELS: Record<ItemStatus, string> = {
  extracted: '已解析',
  incorporated_by_reference: '以引用方式揭露',
  not_applicable: '不適用',
  reserved: 'SEC 保留',
  missing: '未找到',
}

export function statusLabel(status: ItemStatus | string): string {
  return LABELS[status as ItemStatus] ?? String(status).replace(/_/g, ' ')
}
