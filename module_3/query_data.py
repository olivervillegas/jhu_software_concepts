import psycopg

DB_CONFIG = {
    "dbname": "gradcafe",
    "user": "postgres",
    "password": "<REDACTED>", 
    "host": "localhost",
    "port": 5433
}

def run_query(sql):
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()

def get_results():
    return {
        # 1) How many entries applied for Fall 2026?
        "Fall 2026 Applicants": run_query("""
            SELECT COUNT(*)
            FROM applicants
            WHERE TRIM(term) = 'Fall 2026';
        """)[0],

        # 2) % international (not American or Other) to 2 decimals
        "International Percentage": run_query("""
            SELECT
              ROUND(
                (100.0 * COUNT(*) /
                 NULLIF((SELECT COUNT(*) FROM applicants), 0)
                )::numeric,
                2
              )
            FROM applicants
            WHERE us_or_international = 'International';
        """)[0],

        # 3) Avg GPA, GRE, GRE V, GRE AW for those that provide them
        "Average GPA / GRE / GRE-V / GRE-AW (non-null)": run_query("""
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
        """),

        # 4) Avg GPA of American students in Fall 2026
        "Avg GPA (American, Fall 2026)": run_query("""
            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM applicants
            WHERE TRIM(term) = 'Fall 2026'
              AND us_or_international = 'American'
              AND gpa IS NOT NULL;
        """)[0],

        # 5) % of Fall 2026 entries that are acceptances
        "Acceptance Rate (Fall 2026)": run_query("""
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
        """)[0],

        # 6) Avg GPA of Fall 2026 acceptances
        "Avg GPA (Accepted, Fall 2026)": run_query("""
            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM applicants
            WHERE TRIM(term) = 'Fall 2026'
              AND status = 'Accepted'
              AND gpa IS NOT NULL;
        """)[0],

        # 7) How many applied to JHU for Masters in CS? (using program text)
        "JHU Masters CS Applicants": run_query("""
            SELECT COUNT(*)
            FROM applicants
            WHERE program ILIKE '%Johns Hopkins%'
              AND program ILIKE '%Computer Science%'
              AND degree = 'Masters';
        """)[0],

        # 8) 2026 acceptances to Georgetown/MIT/Stanford/CMU for PhD CS (downloaded fields)
        "Fall 2026 Accepted PhD CS at Georgetown/MIT/Stanford/CMU (program text)": run_query("""
            SELECT COUNT(*)
            FROM applicants
            WHERE TRIM(term) = 'Fall 2026'
              AND status = 'Accepted'
              AND degree = 'PhD'
              AND program ILIKE '%Computer Science%'
              AND (
                program ILIKE '%Georgetown%' OR
                program ILIKE '%MIT%' OR
                program ILIKE '%Stanford%' OR
                program ILIKE '%Carnegie Mellon%'
              );
        """)[0],

        # 9) Same as 8 but using LLM fields
        "Fall 2026 Accepted PhD CS at Georgetown/MIT/Stanford/CMU (LLM fields)": run_query("""
            SELECT COUNT(*)
            FROM applicants
            WHERE TRIM(term) = 'Fall 2026'
              AND status = 'Accepted'
              AND degree = 'PhD'
              AND llm_generated_program ILIKE '%Computer Science%'
              AND (
                llm_generated_university ILIKE '%Georgetown%' OR
                llm_generated_university ILIKE '%MIT%' OR
                llm_generated_university ILIKE '%Stanford%' OR
                llm_generated_university ILIKE '%Carnegie Mellon%'
              );
        """)[0],

        # 10) Two additional curiosity questions (examples)
        "Top 5 Universities by # of Entries (LLM)": run_query("""
            SELECT STRING_AGG(x, '; ')
            FROM (
              SELECT llm_generated_university || ': ' || COUNT(*) AS x
              FROM applicants
              WHERE llm_generated_university IS NOT NULL
              GROUP BY llm_generated_university
              ORDER BY COUNT(*) DESC
              LIMIT 5
            ) t;
        """)[0],

        "Acceptance Rate Overall (all terms)": run_query("""
            SELECT
              ROUND(
                (100.0 * (SELECT COUNT(*) FROM applicants WHERE status='Accepted') /
                 NULLIF((SELECT COUNT(*) FROM applicants), 0)
                )::numeric,
                2
              );
        """)[0],
    }

if __name__ == "__main__":
    print("Grad Cafe Database Analysis Results\n")
    results = get_results()
    for question, answer in results.items():
        print(f"{question}: {answer}")
