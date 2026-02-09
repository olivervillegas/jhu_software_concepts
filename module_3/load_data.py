import json
import re
import psycopg
from datetime import datetime

DB_CONFIG = {
    "dbname": "gradcafe",
    "user": "postgres",
    "password": "<REDACTED>", 
    "host": "localhost",
    "port": 5433
}

DATA_PATH = "data/llm_extend_applicant_data.json"  # instructor file (JSONL)


# ---------- Helpers ----------

def load_json_or_jsonl(path: str):
    """Loads either a JSON array or JSONL file."""
    with open(path, "r", encoding="utf-8") as f:
        first = f.read(1)
        f.seek(0)
        if first == "[":
            return json.load(f)
        # JSONL
        return [json.loads(line) for line in f if line.strip()]

def clean_text(v):
    """Strip NULL bytes + whitespace; return None if empty."""
    if v is None:
        return None
    s = str(v).replace("\x00", "").strip()
    return s if s else None

def safe_float(v):
    """Extract first number from a string like 'GPA 3.89' or 'GRE 327'."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"\d+(\.\d+)?", str(v))
    return float(m.group()) if m else None

def parse_date(v):
    """Parse 'January 31, 2026' or ISO '2026-01-31' into a date object."""
    v = clean_text(v)
    if not v:
        return None
    # ISO
    try:
        return datetime.strptime(v, "%Y-%m-%d").date()
    except Exception:
        pass
    # 'January 31, 2026'
    try:
        return datetime.strptime(v, "%B %d, %Y").date()
    except Exception:
        pass
    # Some datasets may have 'Jan 31, 2026'
    try:
        return datetime.strptime(v, "%b %d, %Y").date()
    except Exception:
        pass
    return None

def normalize_status(v):
    v = clean_text(v)
    if not v:
        return None
    low = v.lower()
    if "accept" in low:
        return "Accepted"
    if "reject" in low or "deny" in low:
        return "Rejected"
    if "wait" in low:
        return "Waitlisted"
    if "interview" in low:
        return "Interview"
    return v  # fallback

def normalize_citizenship(v):
    v = clean_text(v)
    if not v:
        return None
    low = v.lower()
    if "international" in low:
        return "International"
    if "american" in low or "domestic" in low or "u.s" in low or "us" == low:
        return "American"
    return v

def normalize_degree(v):
    v = clean_text(v)
    if not v:
        return None
    low = v.lower()
    if "phd" in low:
        return "PhD"
    if "master" in low or "ms" == low or "ma" == low:
        return "Masters"
    return v

def normalize_gpa(v):
    """
    GPA in instructor file can include junk like 'GPA 70'.
    We'll only keep plausible 0.0–4.0 GPAs; otherwise set to None.
    """
    x = safe_float(v)
    if x is None:
        return None
    if 0.0 <= x <= 4.0:
        return x
    return None


# ---------- Main loader ----------

def load_data():
    rows = load_json_or_jsonl(DATA_PATH)
    if not rows:
        raise RuntimeError(f"No rows found in {DATA_PATH}")

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            # Wipe previous bad loads
            cur.execute("TRUNCATE TABLE applicants RESTART IDENTITY;")

            for r in rows:
                program = clean_text(r.get("program"))
                comments = clean_text(r.get("comments"))
                date_added = parse_date(r.get("date_added"))
                url = clean_text(r.get("url"))

                status = normalize_status(r.get("applicant_status"))
                term = clean_text(r.get("semester_year_start"))  # e.g. "Fall 2026"

                us_or_international = normalize_citizenship(r.get("citizenship"))

                gpa = normalize_gpa(r.get("gpa"))
                gre = safe_float(r.get("gre"))
                gre_v = safe_float(r.get("gre_v"))
                gre_aw = safe_float(r.get("gre_aw"))

                degree = normalize_degree(r.get("masters_or_phd"))

                llm_generated_program = clean_text(r.get("llm-generated-program"))
                llm_generated_university = clean_text(r.get("llm-generated-university"))

                cur.execute("""
                    INSERT INTO applicants (
                        program,
                        comments,
                        date_added,
                        url,
                        status,
                        term,
                        us_or_international,
                        gpa,
                        gre,
                        gre_v,
                        gre_aw,
                        degree,
                        llm_generated_program,
                        llm_generated_university
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    program,
                    comments,
                    date_added,
                    url,
                    status,
                    term,
                    us_or_international,
                    gpa,
                    gre,
                    gre_v,
                    gre_aw,
                    degree,
                    llm_generated_program,
                    llm_generated_university
                ))

        conn.commit()


if __name__ == "__main__":
    load_data()
