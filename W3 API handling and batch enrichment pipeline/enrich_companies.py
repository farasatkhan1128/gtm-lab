import time
import csv

# --- Stand-in for a live enrichment API (Apollo/Clearbit shape). ---
# In production, enrich_company() would call the API by domain with your key.
# This dict is what such an API hands back: one nested record per company.
COMPANY_DB = {
    "stripe.com": {
        "name": "Stripe",
        "industry": "Financial Software",
        "location": {"city": "San Francisco", "country": "United States"},
        "employees": 8000,
    },
    "monzo.com": {
        "name": "Monzo",
        "industry": "Banking",
        "location": {"city": "London", "country": "United Kingdom"},
        # note: no 'employees' field — a realistic missing value
    },
    "canva.com": {
        "name": "Canva",
        "industry": "Design Software",
        "location": {"city": "Sydney"},   # note: no 'country' — missing nested value
        "employees": 4000,
    },
}


def enrich_company(domain):
    # --- swap point: in production this is an Apollo/Clearbit GET by domain ---
    record = COMPANY_DB.get(domain)

    # A lookup that finds nothing is the local equivalent of a 404 / no-match.
    if record is None:
        return {"input": domain, "ok": False, "reason": "no match found"}

    # Pull specific fields from the nested record, with fallbacks for missing ones.
    return {
        "input": domain,
        "ok": True,
        "company": record.get("name", "UNKNOWN"),
        "industry": record.get("industry", "UNKNOWN"),
        "city": record.get("location", {}).get("city", "UNKNOWN"),
        "country": record.get("location", {}).get("country", "UNKNOWN"),
        "employees": record.get("employees", 0),
    }


# --- our company inputs (domains, like a real prospecting list) ---
inputs = ["stripe.com", "monzo.com", "canva.com", "notacompany.xyz"]

results = []
failures = []

for domain in inputs:
    print(f"Enriching {domain}...")
    record = enrich_company(domain)

    if record["ok"]:
        results.append(record)
    else:
        failures.append(record)

    time.sleep(0.3)   # kept as a habit; in production this paces real API calls

# --- summary ---
print()
print(f"Enrichment complete: {len(results)} succeeded, {len(failures)} failed, {len(inputs)} total")

print()
print("ENRICHED:")
for r in results:
    print(f"  {r['input']} -> {r['company']} | {r['industry']} | {r['city']}, {r['country']} | {r['employees']:,} staff")

print()
print("REVIEW (failed):")
for f in failures:
    print(f"  {f['input']}: {f['reason']}")

# --- write both streams to CSV (Thursday's component, reused) ---
def write_csv(filename, rows, fieldnames):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    if len(rows) == 0:
        print(f"  {filename}: header only — no rows to write")
    else:
        print(f"  Wrote {len(rows)} rows to {filename}")

print()
print("Writing output files:")
write_csv("companies_enriched.csv", results, ["input", "ok", "company", "industry", "city", "country", "employees"])
write_csv("companies_review.csv", failures, ["input", "ok", "reason"])