"""
Validator
獨立於 parser 的驗證層：重新核對結構不變量，捕捉「parser 說成功、實際卻錯」
的靜默錯誤。輸入 raw_items（乾淨幾何 + spans + confidence）、最終 items
（status 分類）、text、metadata、parse_result，輸出 QualityReport。

設計見 docs（P1 規則集）：
  Rule 0  range 合法性          （raw_items, error）
  Rule 2  順序單調              （raw_items, warning；多 span 路徑降為 info）
  Rule 3' 過大 item            （raw_items, warning）
  Rule 4  必要 item 缺失        （final items, error / warning）
  Rule 5  status↔欄位契約       （final items, error）
  Rule 6  extracted 近乎空      （final items, error）
  Rule 7  文件長度地板          （text, error / warning）
  Rule 8  低信心                （raw_items + parse_result, info）
"""

from __future__ import annotations

import re

from sec_10k_pipeline.models import (
    RawItem,
    ItemResult,
    FilingMetadata,
    QualityReport,
    ValidationFlag,
)
from sec_10k_pipeline.parsers.base import ParseResult
from sec_10k_pipeline.patterns import ITEM_NUMBERS, HTML_TAG_PATTERN

# ── 門檻（皆可調）────────────────────────────────────────────
REQUIRED_CORE_ITEMS = {"1", "2", "3", "5", "7", "8", "9A", "15"}
REQUIRED_UNLESS_SRC_ITEMS = {"1A", "7A"}      # smaller reporting company 豁免
NATURALLY_LARGE_ITEMS = {"1A", "7", "8"}      # 天生大，過大檢查放寬
OVERSIZED_RATIO = 0.45                        # 單一 item 佔全體可讀跨度比例上限
OVERSIZED_MIN_READABLE = 50_000               # 過大檢查的絕對下限（可讀字元）
OVERSIZED_MIN_ITEMS = 6                        # item 太少時不做過大檢查
EXTRACTED_MIN_READABLE = 50                    # extracted 至少要有的可讀字元
DOC_FLOOR_ERROR = 5_000                        # 全文可讀字元低於此 → error
DOC_FLOOR_WARN = 20_000                        # 低於此 → warning
CONFIDENCE_THRESHOLD = 0.7

_ANCHOR_MARKER = re.compile(r"\[\[ANCHOR:[^\]]+\]\]")
_PAGE_MARKER = re.compile(r"\[\[PAGE:\d+\]\]")

_CANONICAL_ORDER = {num: i for i, num in enumerate(ITEM_NUMBERS)}


def _readable_length(text: str) -> int:
    """可讀長度：移除注入標記與 HTML 標籤後的字元數，避免表格 / marker 灌水。"""
    if not text:
        return 0
    cleaned = _ANCHOR_MARKER.sub(" ", text)
    cleaned = _PAGE_MARKER.sub(" ", cleaned)
    cleaned = HTML_TAG_PATTERN.sub(" ", cleaned)
    return len(cleaned.strip())


def _geometry(raw: RawItem) -> list[tuple[int, int]]:
    """取得 RawItem 的字元範圍（統一成 span 清單）。沒有可用幾何時回空 list。"""
    if raw.spans:
        return [(s.start_char, s.end_char) for s in raw.spans]
    if raw.end_char is not None:
        return [(raw.start_char, raw.end_char)]
    return []


class Validator:

    def validate(
        self,
        raw_items: list[RawItem],
        items: list[ItemResult],
        text: str,
        metadata: FilingMetadata,
        parse_result: ParseResult,
    ) -> QualityReport:
        text_len = len(text)
        flags: list[ValidationFlag] = []
        # 多 span 路徑（cross-reference / pdf-style）才會有 spans；regex 不會。
        # 這類文件的 SEC item 物理順序可能合法地不照編號，故順序檢查降為 info。
        has_spans = any(item.spans for item in raw_items)

        flags += self._rule0_range_validity(raw_items, text_len)
        flags += self._rule2_ordering(raw_items, has_spans)
        coverage_ratio = 0.0
        oversized_flags, coverage_ratio = self._rule3_oversized(raw_items, text)
        flags += oversized_flags
        flags += self._rule4_required_missing(items, metadata)
        flags += self._rule5_status_contract(items)
        flags += self._rule6_extracted_empty(items)
        flags += self._rule7_document_length(text)
        flags += self._rule8_low_confidence(raw_items, parse_result)

        return self._build_report(
            flags, items, parse_result, metadata, coverage_ratio
        )

    # ── Rule 0：range 合法性 ───────────────────────────────────
    def _rule0_range_validity(
        self, raw_items: list[RawItem], text_len: int
    ) -> list[ValidationFlag]:
        flags: list[ValidationFlag] = []
        for raw in raw_items:
            for start, end in _geometry(raw):
                if not (0 <= start < end <= text_len):
                    flags.append(ValidationFlag(
                        code="range_invalid",
                        severity="error",
                        item_number=raw.item_number,
                        message=(
                            f"Item {raw.item_number} 的 range 不合法："
                            f"start={start}, end={end}, text_len={text_len}"
                            "（很可能是標題定位錯誤或座標被夾成 0）"
                        ),
                        detail={"start": start, "end": end, "text_len": text_len},
                    ))
        return flags

    # ── Rule 2：順序單調 ───────────────────────────────────────
    def _rule2_ordering(
        self, raw_items: list[RawItem], has_spans: bool
    ) -> list[ValidationFlag]:
        positioned: list[tuple[str, int]] = []
        for raw in raw_items:
            geom = _geometry(raw)
            if geom:
                positioned.append((raw.item_number, geom[0][0]))

        positioned.sort(key=lambda x: _CANONICAL_ORDER.get(x[0], 99))

        severity = "info" if has_spans else "warning"
        flags: list[ValidationFlag] = []
        prev_num, prev_pos = None, -1
        for num, pos in positioned:
            if pos < prev_pos:
                flags.append(ValidationFlag(
                    code="ordering_violation",
                    severity=severity,
                    item_number=num,
                    message=(
                        f"Item {num} 的物理位置({pos})排在前一個 "
                        f"Item {prev_num}({prev_pos})之前，違反編號順序"
                    ),
                    detail={"item_pos": pos, "prev_item": prev_num, "prev_pos": prev_pos},
                ))
            else:
                prev_num, prev_pos = num, pos
        return flags

    # ── Rule 3'：過大 item + coverage ──────────────────────────
    def _rule3_oversized(
        self, raw_items: list[RawItem], text: str
    ) -> tuple[list[ValidationFlag], float]:
        lengths: dict[str, int] = {}
        raw_span_total = 0
        envelope_start, envelope_end = None, None

        for raw in raw_items:
            geom = _geometry(raw)
            if not geom:
                continue
            item_readable = sum(_readable_length(text[s:e]) for s, e in geom)
            lengths[raw.item_number] = item_readable
            for s, e in geom:
                raw_span_total += (e - s)
                envelope_start = s if envelope_start is None else min(envelope_start, s)
                envelope_end = e if envelope_end is None else max(envelope_end, e)

        coverage_ratio = 0.0
        if envelope_start is not None and envelope_end and envelope_end > envelope_start:
            coverage_ratio = round(raw_span_total / (envelope_end - envelope_start), 4)

        flags: list[ValidationFlag] = []
        total_readable = sum(lengths.values())
        if total_readable > 0 and len(lengths) >= OVERSIZED_MIN_ITEMS:
            for num, length in lengths.items():
                if num in NATURALLY_LARGE_ITEMS:
                    continue
                ratio = length / total_readable
                if ratio > OVERSIZED_RATIO and length > OVERSIZED_MIN_READABLE:
                    flags.append(ValidationFlag(
                        code="oversized_item",
                        severity="warning",
                        item_number=num,
                        message=(
                            f"Item {num} 佔全體可讀內容 {ratio:.0%}"
                            f"（{length:,} 字），疑似吞併了漏抓的鄰近 Item"
                        ),
                        detail={"readable_len": length, "ratio": round(ratio, 4)},
                    ))
        return flags, coverage_ratio

    # ── Rule 4：必要 item 缺失 ─────────────────────────────────
    def _rule4_required_missing(
        self, items: list[ItemResult], metadata: FilingMetadata
    ) -> list[ValidationFlag]:
        status_map = {item.item_number: item.status for item in items}
        is_src = bool(
            metadata.filer_category
            and "smaller reporting" in metadata.filer_category.lower()
        )
        # 視為「沒抓到實質內容」的 status
        bad = {"missing", "not_applicable", "reserved"}

        flags: list[ValidationFlag] = []
        for num in REQUIRED_CORE_ITEMS:
            status = status_map.get(num)
            if status is None or status in bad:
                flags.append(ValidationFlag(
                    code="required_item_missing",
                    severity="error",
                    item_number=num,
                    message=f"核心必要 Item {num} 未成功抽取（status={status}）",
                    detail={"status": status},
                ))
        if not is_src:
            for num in REQUIRED_UNLESS_SRC_ITEMS:
                status = status_map.get(num)
                if status is None or status in bad:
                    flags.append(ValidationFlag(
                        code="recommended_item_missing",
                        severity="warning",
                        item_number=num,
                        message=(
                            f"Item {num} 未抽取（status={status}）；"
                            "非 smaller reporting company 通常應有此 Item"
                        ),
                        detail={"status": status},
                    ))
        return flags

    # ── Rule 5：status↔欄位契約 ────────────────────────────────
    def _rule5_status_contract(self, items: list[ItemResult]) -> list[ValidationFlag]:
        flags: list[ValidationFlag] = []
        for item in items:
            num, status = item.item_number, item.status
            has_content = bool(item.content_text and item.content_text.strip())
            has_range = item.char_range is not None

            if status == "extracted":
                if not has_content or not has_range:
                    flags.append(ValidationFlag(
                        code="status_field_contract",
                        severity="error",
                        item_number=num,
                        message=(
                            f"Item {num} status=extracted 但缺內容或 range"
                            f"（has_content={has_content}, has_range={has_range}）"
                        ),
                        detail={"status": status, "has_content": has_content, "has_range": has_range},
                    ))
            elif status in ("reserved", "not_applicable", "missing"):
                if has_content or has_range:
                    flags.append(ValidationFlag(
                        code="status_field_contract",
                        severity="error",
                        item_number=num,
                        message=(
                            f"Item {num} status={status} 卻帶有內容或 range"
                            f"（has_content={has_content}, has_range={has_range}）"
                        ),
                        detail={"status": status, "has_content": has_content, "has_range": has_range},
                    ))
            # incorporated_by_reference：契約寬鬆，不檢查
        return flags

    # ── Rule 6：extracted 近乎空 ───────────────────────────────
    def _rule6_extracted_empty(self, items: list[ItemResult]) -> list[ValidationFlag]:
        flags: list[ValidationFlag] = []
        for item in items:
            if item.status != "extracted":
                continue
            readable = _readable_length(item.content_text or "")
            if readable < EXTRACTED_MIN_READABLE:
                flags.append(ValidationFlag(
                    code="extracted_empty",
                    severity="error",
                    item_number=item.item_number,
                    message=(
                        f"Item {item.item_number} status=extracted 但可讀內容僅 "
                        f"{readable} 字，幾乎為空"
                    ),
                    detail={"readable_len": readable},
                ))
        return flags

    # ── Rule 7：文件長度地板 ───────────────────────────────────
    def _rule7_document_length(self, text: str) -> list[ValidationFlag]:
        readable = _readable_length(text)
        if readable < DOC_FLOOR_ERROR:
            return [ValidationFlag(
                code="document_too_short",
                severity="error",
                message=(
                    f"全文可讀長度僅 {readable:,} 字，遠低於正常 10-K，"
                    "很可能抓錯主文件或 preprocess 清掉了內容"
                ),
                detail={"readable_len": readable},
            )]
        if readable < DOC_FLOOR_WARN:
            return [ValidationFlag(
                code="document_short",
                severity="warning",
                message=f"全文可讀長度 {readable:,} 字偏短，建議人工確認",
                detail={"readable_len": readable},
            )]
        return []

    # ── Rule 8：低信心 ─────────────────────────────────────────
    def _rule8_low_confidence(
        self, raw_items: list[RawItem], parse_result: ParseResult
    ) -> list[ValidationFlag]:
        flags: list[ValidationFlag] = []
        if parse_result.confidence < CONFIDENCE_THRESHOLD:
            flags.append(ValidationFlag(
                code="low_confidence_parse",
                severity="info",
                message=(
                    f"整份解析信心 {parse_result.confidence:.2f} 低於門檻 "
                    f"{CONFIDENCE_THRESHOLD}"
                ),
                detail={"confidence": round(parse_result.confidence, 4)},
            ))
        for raw in raw_items:
            if raw.confidence < CONFIDENCE_THRESHOLD:
                flags.append(ValidationFlag(
                    code="low_confidence_item",
                    severity="info",
                    item_number=raw.item_number,
                    message=f"Item {raw.item_number} 信心 {raw.confidence:.2f} 偏低",
                    detail={"confidence": round(raw.confidence, 4)},
                ))
        return flags

    # ── 聚合 ───────────────────────────────────────────────────
    def _build_report(
        self,
        flags: list[ValidationFlag],
        items: list[ItemResult],
        parse_result: ParseResult,
        metadata: FilingMetadata,
        coverage_ratio: float,
    ) -> QualityReport:
        counts = {"error": 0, "warning": 0, "info": 0}
        for flag in flags:
            counts[flag.severity] += 1

        missing_items = [
            item.item_number for item in items if item.status == "missing"
        ]
        missing_required = sorted(
            {
                flag.item_number
                for flag in flags
                if flag.code in ("required_item_missing", "recommended_item_missing")
                and flag.item_number is not None
            },
            key=lambda n: _CANONICAL_ORDER.get(n, 99),
        )
        found_count = sum(
            1 for item in items
            if item.status in ("extracted", "incorporated_by_reference")
        )

        errors, warnings = counts["error"], counts["warning"]
        score = max(0.0, round(1.0 - 0.2 * errors - 0.05 * warnings, 4))

        return QualityReport(
            is_valid=errors == 0,
            score=score,
            parser_name=parse_result.parser_name,
            parser_confidence=round(parse_result.confidence, 4),
            expected_item_count=len(items),
            found_item_count=found_count,
            missing_items=missing_items,
            missing_required_items=missing_required,
            coverage_ratio=coverage_ratio,
            counts=counts,
            flags=flags,
        )
