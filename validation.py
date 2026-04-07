"""Input validation and sanitization (stdlib only). Tune limits via constants below."""
from __future__ import annotations

import re
from typing import Any

# --- Limits (adjust to your policy) ---
MAX_CNR_LEN = 64
# eCourts CNR is often 16 chars; raise to 16 if you want to reject shorter test inputs.
MIN_CNR_LEN = 6
MAX_TEXT_FIELD = 500
MAX_COURT_FIELD = 600
MAX_EMAIL_LEN = 320
MAX_PHONE_LEN = 40
MAX_HISTORY_JSON_CHARS = 2_000_000
MAX_HISTORY_ROWS = 2000
MAX_JUDGE_LEN = 500
MAX_PURPOSE_LEN = 2000
MAX_EVENT_TITLE = 500
MAX_NOTES = 8000
MAX_EVENT_TYPE = 120
MAX_USERNAME_LEN = 20
MAX_PASSWORD_LEN = 20

# Indian eCourts CNR-style: letters, digits, hyphens; no arbitrary punctuation.
CNR_PATTERN = re.compile(r"^[A-Za-z0-9\-]+$")


def sanitize_str(value: Any, max_len: int, *, optional: bool = False) -> tuple[str | None, str | None]:
    """Return (cleaned_str, error_message). cleaned None only if optional and empty."""
    if value is None:
        value = ""
    s = " ".join(str(value).split()) if isinstance(value, str) else str(value).strip()
    if not s:
        if optional:
            return "", None
        return None, "This field cannot be empty."
    if len(s) > max_len:
        return None, f"Text is too long (max {max_len} characters)."
    return s, None


def validate_cnr(raw: Any) -> tuple[str | None, str | None]:
    s, err = sanitize_str(raw, MAX_CNR_LEN, optional=False)
    if err or s is None:
        return None, err or "Invalid CNR."
    compact = s.replace(" ", "")
    if len(compact) < MIN_CNR_LEN:
        return None, f"CNR is too short (min {MIN_CNR_LEN} characters)."
    if not CNR_PATTERN.match(compact):
        return None, "CNR may only contain letters, digits, and hyphens."
    return compact, None


def validate_email_optional(raw: Any) -> tuple[str | None, str | None]:
    s, err = sanitize_str(raw, MAX_EMAIL_LEN, optional=True)
    if err:
        return None, err
    assert s is not None
    if not s:
        return "", None
    if "@" not in s:
        return None, "Email does not look valid."
    return s, None


def validate_email_required(raw: Any) -> tuple[str | None, str | None]:
    s, err = sanitize_str(raw, MAX_EMAIL_LEN, optional=False)
    if err or s is None:
        return None, err or "Email is required."
    if "@" not in s:
        return None, "Email does not look valid."
    return s, None


def validate_history_list(rows: Any) -> tuple[list[dict[str, Any]] | None, str | None]:
    if not isinstance(rows, list):
        return None, "Case history must be a list."
    if len(rows) > MAX_HISTORY_ROWS:
        return None, f"Too many history rows (max {MAX_HISTORY_ROWS})."
    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            return None, f"History row {i + 1} is invalid."
        for key in ("judge", "hearing_date"):
            if key not in row:
                return None, f"History row {i + 1} is missing '{key}'."
        judge, je = sanitize_str(row.get("judge"), MAX_JUDGE_LEN, optional=True)
        if je:
            return None, je
        purpose, pe = sanitize_str(row.get("purpose"), MAX_PURPOSE_LEN, optional=True)
        if pe:
            return None, pe
        bd, _ = sanitize_str(row.get("business_date"), MAX_TEXT_FIELD, optional=True)
        hd, hde = sanitize_str(row.get("hearing_date"), MAX_TEXT_FIELD, optional=False)
        if hde:
            return None, f"Row {i + 1}: {hde}"
        out.append(
            {
                "judge": judge or "",
                "business_date": bd or "",
                "hearing_date": hd or "",
                "purpose": purpose or "",
            }
        )
    return out, None


def validate_case_save(
    case_title: str,
    client_name: str,
    phone: str,
    email: str,
    cnr: str,
    regno: str,
    court: str,
    filing: str,
    ctype: str,
    next_hearing_date: str,
    case_stage: str,
    sub_stage: str,
) -> tuple[dict[str, str] | None, str | None]:
    fields = [
        ("case_title", case_title, MAX_TEXT_FIELD, False),
        ("client_name", client_name, MAX_TEXT_FIELD, False),
        ("phone", phone, MAX_PHONE_LEN, False),
        ("cnr", cnr, MAX_CNR_LEN, False),
        ("regno", regno, MAX_TEXT_FIELD, True),
        ("court", court, MAX_COURT_FIELD, True),
        ("filing", filing, MAX_TEXT_FIELD, True),
        ("ctype", ctype, MAX_TEXT_FIELD, True),
        ("next_hearing_date", next_hearing_date, MAX_TEXT_FIELD, True),
        ("case_stage", case_stage, MAX_TEXT_FIELD, True),
        ("sub_stage", sub_stage, MAX_TEXT_FIELD, True),
    ]
    cleaned: dict[str, str] = {}
    for name, raw, mx, opt in fields:
        s, err = sanitize_str(raw, mx, optional=opt)
        if err:
            return None, err
        cleaned[name] = s or ""
    cnr_ok, cnr_err = validate_cnr(cleaned["cnr"])
    if cnr_err:
        return None, cnr_err
    cleaned["cnr"] = cnr_ok or ""
    em, eme = validate_email_required(email)
    if eme:
        return None, eme
    cleaned["email"] = em or ""
    return cleaned, None


def validate_appointment(
    event_title: str,
    event_date: str,
    event_type: str,
    notes: str,
) -> tuple[dict[str, str] | None, str | None]:
    title, te = sanitize_str(event_title, MAX_EVENT_TITLE, optional=False)
    if te:
        return None, te
    date_s, de = sanitize_str(event_date, MAX_TEXT_FIELD, optional=False)
    if de:
        return None, de
    etype, ete = sanitize_str(event_type, MAX_EVENT_TYPE, optional=False)
    if ete:
        return None, ete
    n, ne = sanitize_str(notes, MAX_NOTES, optional=True)
    if ne:
        return None, ne
    return {
        "event_title": title or "",
        "event_date": date_s or "",
        "event_type": etype or "",
        "notes": n or "",
    }, None


def validate_login(username: str, password: str) -> tuple[tuple[str, str] | None, str | None]:
    u = (username or "").strip()
    p = password if password is not None else ""
    if not u:
        return None, "Username is required."
    if not p:
        return None, "Password is required."
    if len(u) > MAX_USERNAME_LEN:
        return None, f"Username is too long (max {MAX_USERNAME_LEN} characters)."
    if len(p) > MAX_PASSWORD_LEN:
        return None, f"Password is too long (max {MAX_PASSWORD_LEN} characters)."
    return (u, p), None
