"""Normalize date strings to DD-MM-YYYY for database storage."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

_OUT = "%d-%m-%Y"


def _try_parse(s: str) -> Optional[str]:
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime(_OUT)
        except ValueError:
            continue
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})", s.strip())
    if m:
        d, mo, y = m.groups()
        try:
            return datetime(int(y), int(mo), int(d)).strftime(_OUT)
        except ValueError:
            pass
    t = s.replace(",", "").strip()
    m = re.match(r"^(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s+(\d{4})$", t, re.I)
    if m:
        d, mon, y = m.groups()
        for fmt in ("%d %B %Y", "%d %b %Y"):
            try:
                return datetime.strptime(f"{d} {mon} {y}", fmt).strftime(_OUT)
            except ValueError:
                continue
    return None


def normalize_date_for_db(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    s = " ".join(str(value).split())
    if not s:
        return None
    parsed = _try_parse(s)
    return parsed if parsed is not None else s
