# make_analysis_pdf.py
# Multi-page PDF generator using ONLY stdlib + psycopg.
# Fixes pagination by keeping each question as a block (no page starts with "Answer:" randomly).

from __future__ import annotations

import datetime as _dt
import psycopg

DB_CONFIG = {
    "dbname": "gradcafe",
    "user": "postgres",
    "password": "<REDACTED>",
    "host": "localhost",
    "port": 5433            
}

OUTPUT_PDF = "analysis_results.pdf"


def run_query(sql: str):
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
            if row is None:
                return None
            if isinstance(row, tuple) and len(row) == 1:
                return row[0]
            return row


def build_items():
    Q = []

    def add(question: str, sql: str, why: str):
        ans = run_query(sql)
        Q.append({
            "question": question.strip(),
            "sql": sql.strip(),
            "why": why.strip(),
            "answer": str(ans)
        })

    add(
        "1) How many entries do you have in your database who have applied for Fall 2026?",
        """
        SELECT COUNT(*)
        FROM applicants
        WHERE TRIM(term) = 'Fall 2026';
        """,
        "Counts all rows where term equals 'Fall 2026' (TRIM avoids trailing-space mismatches)."
    )

    add(
        "2) What percentage of entries are from international students (to two decimal places)?",
        """
        SELECT
          ROUND(
            (100.0 * COUNT(*) /
             NULLIF((SELECT COUNT(*) FROM applicants), 0)
            )::numeric,
            2
          )
        FROM applicants
        WHERE us_or_international = 'International';
        """,
        "International count divided by total entries times 100, rounded to 2 decimals. NULLIF prevents divide-by-zero."
    )

    add(
        "3) What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?",
        """
        SELECT
          ROUND(AVG(gpa)::numeric, 2),
          ROUND(AVG(gre)::numeric, 2),
          ROUND(AVG(gre_v)::numeric, 2),
          ROUND(AVG(gre_aw)::numeric, 2)
        FROM applicants
        WHERE gpa IS NOT NULL
           OR gre IS NOT NULL
           OR gre_v IS NOT NULL
           OR gre_aw IS NOT NULL;
        """,
        "Averages numeric columns; restricts to rows where at least one metric exists."
    )

    add(
        "4) What is the average GPA of American students in Fall 2026?",
        """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE TRIM(term) = 'Fall 2026'
          AND us_or_international = 'American'
          AND gpa IS NOT NULL;
        """,
        "Filters to Fall 2026 + American + non-null GPA, then averages."
    )

    add(
        "5) What percent of entries for Fall 2026 are Acceptances (to two decimal places)?",
        """
        SELECT
          CASE
            WHEN (SELECT COUNT(*) FROM applicants WHERE TRIM(term) = 'Fall 2026') = 0
            THEN 0
            ELSE ROUND(
              (100.0 * COUNT(*) /
               (SELECT COUNT(*) FROM applicants WHERE TRIM(term) = 'Fall 2026')
              )::numeric,
              2
            )
          END
        FROM applicants
        WHERE TRIM(term) = 'Fall 2026'
          AND status = 'Accepted';
        """,
        "Accepted count divided by total Fall 2026 count times 100; CASE prevents division by zero."
    )

    add(
        "6) What is the average GPA of applicants who applied for Fall 2026 who are Acceptances?",
        """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE TRIM(term) = 'Fall 2026'
          AND status = 'Accepted'
          AND gpa IS NOT NULL;
        """,
        "Filters to accepted Fall 2026 applicants with GPA and averages."
    )

    add(
        "7) How many entries are from applicants who applied to JHU for a masters degree in Computer Science?",
        """
        SELECT COUNT(*)
        FROM applicants
        WHERE program ILIKE '%Johns Hopkins%'
          AND program ILIKE '%Computer Science%'
          AND degree = 'Masters';
        """,
        "Case-insensitive matching with ILIKE on program text and restricts degree to Masters."
    )

    add(
        "8) How many Fall 2026 acceptances are from applicants who applied to Georgetown, MIT, Stanford, or CMU for a PhD in CS? (downloaded fields)",
        """
        SELECT COUNT(*)
        FROM applicants
        WHERE TRIM(term) = 'Fall 2026'
          AND degree = 'PhD'
          AND status = 'Accepted'
          AND program ILIKE '%Computer Science%'
          AND (
            program ILIKE '%Georgetown%' OR
            program ILIKE '%MIT%' OR
            program ILIKE '%Stanford%' OR
            program ILIKE '%Carnegie Mellon%'
          );
        """,
        "Filters by term/degree/status and matches university keywords inside the original program text."
    )

    add(
        "9) Do the numbers for question 8 change if you use LLM-generated fields?",
        """
        SELECT COUNT(*)
        FROM applicants
        WHERE TRIM(term) = 'Fall 2026'
          AND degree = 'PhD'
          AND status = 'Accepted'
          AND llm_generated_program ILIKE '%Computer Science%'
          AND (
            llm_generated_university ILIKE '%Georgetown%' OR
            llm_generated_university ILIKE '%MIT%' OR
            llm_generated_university ILIKE '%Stanford%' OR
            llm_generated_university ILIKE '%Carnegie Mellon%'
          );
        """,
        "Same as Q8 but matches CS + universities using normalized LLM-generated fields."
    )

    add(
        "10) Additional Question: What are the top 5 universities by number of entries (LLM university field)?",
        """
        SELECT STRING_AGG(x, '; ')
        FROM (
          SELECT llm_generated_university || ': ' || COUNT(*) AS x
          FROM applicants
          WHERE llm_generated_university IS NOT NULL
          GROUP BY llm_generated_university
          ORDER BY COUNT(*) DESC
          LIMIT 5
        ) t;
        """,
        "Counts entries per LLM-normalized university and returns the top 5 as a readable summary string."
    )

    add(
        "11) Additional Question: What is the overall acceptance rate across all terms (to two decimals)?",
        """
        SELECT
          ROUND(
            (100.0 * (SELECT COUNT(*) FROM applicants WHERE status='Accepted') /
             NULLIF((SELECT COUNT(*) FROM applicants), 0)
            )::numeric,
            2
          );
        """,
        "Computes accepted / total * 100 and rounds to 2 decimals. NULLIF prevents divide-by-zero."
    )

    return Q


# ------------------ RAW PDF HELPERS ------------------

def _pdf_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap(text: str, width: int) -> list[str]:
    out = []
    for para in str(text).split("\n"):
        para = para.rstrip()
        if not para:
            out.append("")
            continue
        words = para.split()
        line = ""
        for w in words:
            if not line:
                line = w
            elif len(line) + 1 + len(w) <= width:
                line += " " + w
            else:
                out.append(line)
                line = w
        if line:
            out.append(line)
    return out


def _make_header_lines() -> list[str]:
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    return [
        "Grad Cafe Data Analysis (Module 3)",
        f"Generated: {now}",
        ""
    ]


def _make_block_lines(block: dict) -> list[str]:
    lines = []
    lines.append(block["question"])
    lines.append(f"Answer: {block['answer']}")
    lines.append("SQL:")
    for l in block["sql"].splitlines():
        lines.append("  " + l.rstrip())
    lines.append("Why this query:")
    for l in _wrap(block["why"], 95):
        lines.append("  " + l)
    lines.append("")
    lines.append("-" * 95)
    lines.append("")
    return lines


def _paginate_blocks(header: list[str], blocks: list[list[str]], lines_per_page: int) -> list[list[str]]:
    pages = []
    current = []
    remaining = lines_per_page

    # Always start each page with header
    def start_new_page():
        nonlocal current, remaining
        current = header.copy()
        remaining = lines_per_page - len(current)

    def finish_page():
        nonlocal current
        pages.append(current)

    start_new_page()

    for block_lines in blocks:
        # If block fits on current page, add it
        if len(block_lines) <= remaining:
            current.extend(block_lines)
            remaining -= len(block_lines)
            continue

        # If block doesn't fit, start a new page
        finish_page()
        start_new_page()

        # If block still doesn't fit on an empty page, we must split it
        if len(block_lines) > remaining:
            idx = 0
            first_chunk = True
            while idx < len(block_lines):
                if remaining <= 0:
                    finish_page()
                    start_new_page()
                    first_chunk = False

                # take as many lines as possible
                take = min(remaining, len(block_lines) - idx)
                chunk = block_lines[idx: idx + take]

                # If this is a continuation page and the chunk starts mid-block, label it
                if not first_chunk and current == header.copy():
                    current.append("(continued)")
                    remaining -= 1

                current.extend(chunk)
                remaining -= take
                idx += take

            continue

        # otherwise add whole block
        current.extend(block_lines)
        remaining -= len(block_lines)

    # last page
    if current:
        pages.append(current)

    return pages


def _build_content_stream(page_lines: list[str], left: int, top: int, leading: int) -> bytes:
    ops = []
    ops.append("BT")
    ops.append("/F1 10 Tf")
    ops.append(f"{left} {top} Td")
    for line in page_lines:
        ops.append(f"({_pdf_escape(line)}) Tj")
        ops.append(f"0 -{leading} Td")
    ops.append("ET")
    return ("\n".join(ops)).encode("latin-1", "replace")


def write_pdf(path: str):
    # Letter page size
    page_w, page_h = 612, 792

    # Layout
    left_margin = 54
    top_start = 740
    bottom_margin = 54
    leading = 12

    usable_height = top_start - bottom_margin
    lines_per_page = int(usable_height // leading)

    header = _make_header_lines()
    blocks = [_make_block_lines(b) for b in build_items()]
    pages_text = _paginate_blocks(header, blocks, lines_per_page)

    # Objects:
    # 1 Catalog
    # 2 Pages
    # 3 Font
    # For each page i:
    #   Page obj: 4 + 2*i
    #   Content obj: 5 + 2*i
    objs: list[tuple[int, bytes]] = []

    def add_obj(n: int, data: bytes):
        objs.append((n, data))

    add_obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    add_obj(3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_obj_ids = []
    base = 4

    for i, page_lines in enumerate(pages_text):
        page_id = base + 2 * i
        content_id = base + 2 * i + 1
        page_obj_ids.append(page_id)

        content = _build_content_stream(page_lines, left_margin, top_start, leading)
        add_obj(content_id, b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" +
                content + b"\nendstream")

        page_dict = (
            f"<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {page_w} {page_h}] "
            f"/Resources << /Font << /F1 3 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        ).encode("ascii")
        add_obj(page_id, page_dict)

    kids = " ".join([f"{pid} 0 R" for pid in page_obj_ids]).encode("ascii")
    pages_dict = b"<< /Type /Pages /Kids [" + kids + b"] /Count " + str(len(page_obj_ids)).encode("ascii") + b" >>"
    add_obj(2, pages_dict)

    # Write with xref
    out = bytearray()
    out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets = {0: 0}
    objs.sort(key=lambda t: t[0])

    for n, data in objs:
        offsets[n] = len(out)
        out.extend(f"{n} 0 obj\n".encode("ascii"))
        out.extend(data)
        out.extend(b"\nendobj\n")

    xref_pos = len(out)
    max_obj = max(offsets.keys())

    out.extend(b"xref\n")
    out.extend(f"0 {max_obj + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for i in range(1, max_obj + 1):
        off = offsets.get(i, 0)
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    out.extend(b"trailer\n")
    out.extend(f"<< /Size {max_obj + 1} /Root 1 0 R >>\n".encode("ascii"))
    out.extend(b"startxref\n")
    out.extend(f"{xref_pos}\n".encode("ascii"))
    out.extend(b"%%EOF\n")

    with open(path, "wb") as f:
        f.write(out)


if __name__ == "__main__":
    write_pdf(OUTPUT_PDF)
    print(f"✅ Wrote {OUTPUT_PDF}")
