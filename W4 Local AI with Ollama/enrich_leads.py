import csv
import os
from validated import get_validated

# --- Paths: read from project root, write back to project root ---
# We're running from inside "W4 Local AI with Ollama", so go up one level to gtm-lab
ROOT = os.path.dirname(os.getcwd())
INPUT_FILE  = os.path.join(ROOT, "companies_enriched.csv")
OUTPUT_FILE = os.path.join(ROOT, "companies_ai_enriched.csv")


def enrich_file():
    # 1. READ every row into a list of dicts (Week 3 skill: DictReader)
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} companies from {INPUT_FILE}")

    enriched_rows = []

    # 2. For each row, generate the AI fields
    for i, row in enumerate(rows, start=1):
        company  = row["company"]
        industry = row["industry"]
        print(f"[{i}/{len(rows)}] Enriching {company} ...")

        try:
            ai = get_validated(company, industry)
            row["ai_summary"]      = ai.get("summary", "")
            row["ai_pain_point"]   = ai.get("pain_point", "")
            row["ai_outreach"]     = ai.get("outreach_line", "")
        except Exception as e:
            # If one company fails, don't kill the whole run — log it and move on
            print(f"    [WARN] {company} failed: {e}")
            row["ai_summary"]    = ""
            row["ai_pain_point"] = ""
            row["ai_outreach"]   = ""

        enriched_rows.append(row)

    # 3. WRITE everything out to a new CSV (Week 3 skill: DictWriter)
    fieldnames = list(enriched_rows[0].keys())   # original columns + 3 new ones
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched_rows)

    print(f"\nDone. Wrote {len(enriched_rows)} enriched rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    enrich_file()