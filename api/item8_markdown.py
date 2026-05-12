from __future__ import annotations

from typing import Any

from sec_10k_pipeline.item8_xbrl_facts import get_item8_xbrl_facts, USER_AGENT
from sec_10k_pipeline.render_item8_markdown import render_markdown

__all__ = ["get_item8_markdown"]


def get_item8_markdown(
    cik: str,
    accession_number: str,
    mode: str = "statements_and_notes",
    user_agent: str = USER_AGENT,
) -> str:
    payload = get_item8_xbrl_facts(cik, accession_number, mode=mode, user_agent=user_agent)
    return render_markdown(payload)
