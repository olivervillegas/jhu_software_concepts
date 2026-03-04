from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _parse_date(value: object) -> Optional[date]:
    """
    Parse date strings in either:
    - YYYY-MM-DD
    - Month DD, YYYY  (e.g., January 31, 2026)

    Returns None if it cannot parse.
    """
    if not value:
        return None

    text = str(value).strip()

    for fmt in ("%Y-%m-%d", "%B %d, %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None


def load_all(path: str) -> List[Dict]:
    """Load a JSON array file or JSONL file from disk."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing seed JSON: {p.resolve()}")

    text = p.read_text(encoding="utf-8").strip()
    if not text: # pragma: no cover
        return []

    if text.startswith("["):
        return json.loads(text)

    return [json.loads(line) for line in text.splitlines() if line.strip()]


def incremental_from_watermark(rows: List[Dict],
                               last_seen: Optional[str]) -> Tuple[List[Dict], Optional[str]]:
    """
    Filter rows newer than last_seen. Watermark is ISO date string 'YYYY-MM-DD'.
    Returns (new_rows, new_last_seen).
    """
    new_rows: List[Dict] = []
    max_seen: Optional[str] = last_seen

    for row in rows: # pragma: no cover
        parsed = _parse_date(row.get("date_added"))
        if parsed is None:
            continue

        iso = parsed.isoformat()
        if last_seen is None or iso > last_seen:
            new_rows.append(row)
            if max_seen is None or iso > max_seen:
                max_seen = iso

    return new_rows, max_seen
