# D:\gtm-lab\W5 Full Pipeline Integration\batch_runner.py
import requests
import time
import random

PROCESS_URL = "http://localhost:5000/process"
COMMIT_URL = "http://localhost:5000/commit"

# --- generate 50 varied synthetic companies ---
industries = ["Fintech", "Software", "Design", "Retail", "Healthcare", "HR Software"]
countries = ["United States", "United Kingdom", "Australia", "Denmark", "Brazil", "Germany"]
sizes = [80, 300, 900, 1200, 2500, 8000]

companies = []
for i in range(1, 51):
    companies.append({
        "company": f"TestCo {i}",
        "domain": f"testco{i}.com",
        "industry": random.choice(industries),
        "country": random.choice(countries),
        "employees": random.choice(sizes),
    })

# --- run each company through the pipeline ---
processed, committed, failed, needs_review = 0, 0, 0, 0

for i, company in enumerate(companies, start=1):
    name = company["company"]
    print(f"[{i:>2}/50] {name:<12} ", end="")

    # 1) enrich via /process
    try:
        r = requests.post(PROCESS_URL, json=company, timeout=60)
        r.raise_for_status()
        enriched = r.json()
        processed += 1
    except Exception as e:
        print(f"PROCESS FAILED — {e}")
        failed += 1
        continue

    # flag leads where the AI fell back
    if enriched.get("outreach_line") == "[NEEDS REVIEW]":
        needs_review += 1
        review_tag = " [NEEDS REVIEW]"
    else:
        review_tag = ""

    # 2) save via /commit
    try:
        r = requests.post(COMMIT_URL, json=enriched, timeout=30)
        r.raise_for_status()
        committed += 1
        print(f"score {enriched.get('icp_score'):>3} | tier {enriched.get('tier')} | saved{review_tag}")
    except Exception as e:
        print(f"COMMIT FAILED — {e}")
        failed += 1
        continue

    time.sleep(0.5)  # pace Ollama so it isn't overwhelmed

# --- summary ---
print("\n" + "=" * 50)
print(f"Batch complete: {len(companies)} companies")
print(f"  Processed:      {processed}")
print(f"  Committed:      {committed}")
print(f"  Failed:         {failed}")
print(f"  Needs review:   {needs_review} (AI fell back)")
print("=" * 50)