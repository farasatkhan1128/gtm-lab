import csv


# ---------- FUNCTION 1: clean a company name ----------
def clean_company_name(name):
    name = name.strip()
    name = name.replace(" Limited", "")
    name = name.replace(" Ltd", "")
    name = name.replace(" ltd", "")
    name = name.title()
    return name


# ---------- FUNCTION 2: score a lead ----------
def score_lead(lead):
    score = 0
    reasons = []

    if lead["country"] == "United Kingdom":
        score += 25
        reasons.append("UK market")

    if lead["industry"] == "Beauty":
        score += 30
        reasons.append("target industry (beauty)")

    if lead["employees"] >= 20:
        score += 30
        reasons.append("suitable team size")

    if score >= 80:
        tier = "Tier 1"
    elif score >= 50:
        tier = "Tier 2"
    else:
        tier = "Tier 3"

    reason = ", ".join(reasons)

    return {
        "icp_score": score,
        "tier": tier,
        "reason": reason
    }


# ---------- STEP 1: read the raw file ----------
with open("W2 Python for GTM Data/leads.csv", "r") as file:
    leads = list(csv.DictReader(file))


# ---------- STEP 2: clean, dedupe, validate, score ----------
seen_domains = set()
clean_leads = []
review_leads = []

for lead in leads:
    domain = lead["domain"].strip().lower()

    # skip duplicates
    if domain in seen_domains:
        print(f"DUPLICATE skipped: {lead['company_name']}")
        continue

    seen_domains.add(domain)

    # clean
    lead["company_name"] = clean_company_name(lead["company_name"])
    lead["domain"] = domain

    # validate
    if not lead["employees"]:
        print(f"MISSING employees: {lead['company_name']} -> sent to review")
        review_leads.append(lead)
        continue

    # convert text to number
    lead["employees"] = int(lead["employees"])

    # score
    result = score_lead(lead)
    lead["icp_score"] = result["icp_score"]
    lead["tier"] = result["tier"]
    lead["reason"] = result["reason"]

    clean_leads.append(lead)


# ---------- STEP 3: sort highest score first ----------
clean_leads.sort(key=lambda x: x["icp_score"], reverse=True)


# ---------- STEP 4: report ----------
print(f"\nStarted with {len(leads)} leads")
print(f"Clean: {len(clean_leads)}")
print(f"Needs review: {len(review_leads)}")


# ---------- STEP 5: write the scored file ----------
with open("W2 Python for GTM Data/leads_scored.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=[
        "company_name", "domain", "industry", "country", "employees",
        "icp_score", "tier", "reason"
    ])
    writer.writeheader()
    writer.writerows(clean_leads)


# ---------- STEP 6: write the review file ----------
with open("W2 Python for GTM Data/leads_review.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=[
        "company_name", "domain", "industry", "country", "employees"
    ])
    writer.writeheader()
    writer.writerows(review_leads)

print("Wrote leads_scored.csv and leads_review.csv")


# ---------- STEP 7: show the ranking ----------
print("\n--- SCORED LEADS (highest first) ---")
for lead in clean_leads:
    print(f"{lead['tier']} | {lead['icp_score']} | {lead['company_name']} | {lead['reason']}")