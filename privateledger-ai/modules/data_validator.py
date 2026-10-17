import datetime
import re
from typing import Dict, Any


def _parse_date(date_str: str) -> str:
    """Attempt to parse a date string into ISO format (YYYY-MM-DD).
    Returns the original string if parsing fails.
    """
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(date_str, fmt).date().isoformat()
        except ValueError:
            continue
    # Fallback: try to extract digits
    match = re.search(r"(\d{4})[-/]?(\d{1,2})[-/]?(\d{1,2})", date_str)
    if match:
        y, m, d = match.groups()
        try:
            return datetime.date(int(y), int(m), int(d)).isoformat()
        except ValueError:
            pass
    return date_str  # leave as‑is if we cannot parse


def _to_float(value: Any) -> float:
    """Convert a value to float safely. Returns 0.0 on failure.
    """
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def validate_and_normalize(record: Dict[str, Any]) -> Dict[str, Any]:
    """Validate extracted record fields and normalise types.

    Expected keys (may be missing): vendor, invoice_number, date, subtotal,
    tax, total, currency, category, payment_method, description, filename,
    status.
    """
    # Ensure required keys exist
    defaults = {
        "vendor": "",
        "invoice_number": "",
        "date": "",
        "subtotal": 0.0,
        "tax": 0.0,
        "total": 0.0,
        "currency": "",
        "category": "",
        "payment_method": "",
        "description": "",
        "filename": record.get("filename", ""),
        "status": "pending",
    }
    normalized = {**defaults, **record}

    # Normalise date
    if isinstance(normalized["date"], str):
        normalized["date"] = _parse_date(normalized["date"]).strip()

    # Normalise numeric fields
    for key in ("subtotal", "tax", "total"):
        normalized[key] = _to_float(normalized.get(key, 0))

    # Trim strings
    for key in ("vendor", "invoice_number", "currency", "category", "payment_method", "description"):
        if isinstance(normalized[key], str):
            normalized[key] = normalized[key].strip()

    return normalized
