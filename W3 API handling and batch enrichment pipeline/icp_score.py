import requests
import time


def size_band(employees):
    """Turn a raw employee count into a size band."""
    if employees >= 5000:
        return "Enterprise"
    elif employees >= 1000:
        return "Mid-market"
    else:
        return "Startup"


def industry_points(industry):
    """Score industry fit — our product sells best to fintech & software (0-40)."""
    if industry == "Fintech":
        return 40
    elif industry in ("HR Software", "Software"):
        return 30
    elif industry == "Design":
        return 15
    else:
        return 5


def country_points(country):
    """Score country fit — core markets score highest (0-30)."""
    if country in ("United States", "United Kingdom"):
        return 30
    elif country in ("Australia", "Denmark", "Canada", "Germany", "Ireland"):
        return 15
    else:
        return 5


def size_points(employees):
    """Score company size — bigger = more budget/seats (0-30)."""
    band = size_band(employees)
    if band == "Enterprise":
        return 30
    elif band == "Mid-market":
        return 25
    else:  # Startup
        return 10


def score_company(company):
    """Take a company dict, return it enriched with icp_score, tier, and reason."""
    ind_pts = industry_points(company["industry"])
    ctry_pts = country_points(company["country"])
    sz_pts = size_points(company["employees"])
    total = ind_pts + ctry_pts + sz_pts

    # total is out of 100 -> assign a tier
    if total >= 80:
        tier = "A"
    elif total >= 60:
        tier = "B"
    else:
        tier = "C"

    # build a human-readable reason
    band = size_band(company["employees"])
    reason = (f"{company['industry']} ({ind_pts}) + "
              f"{company['country']} ({ctry_pts}) + "
              f"{band} ({sz_pts}) = {total}")

    # return the original company plus the new scoring fields
    return {
        **company,
        "icp_score": total,
        "tier": tier,
        "reason": reason,
    }


# ─── Everything below only runs when you run THIS file directly ───
# ─── (python icp_score.py). It does NOT run when service.py imports it. ───
if __name__ == "__main__":
    # --- test each scorer ---
    print("Industry:")
    for ind in ["Fintech", "Software", "Design", "Retail"]:
        print(f"  {ind:>12} -> {industry_points(ind)} pts")

    print("\nCountry:")
    for c in ["United States", "Australia", "Brazil"]:
        print(f"  {c:>14} -> {country_points(c)} pts")

    print("\nSize:")
    for n in [8000, 2500, 400]:
        print(f"  {n:>5} employees ({size_band(n)}) -> {size_points(n)} pts")

    # --- test on a few companies ---
    test_companies = [
        {"company": "Stripe", "industry": "Fintech",  "country": "United States",  "employees": 8000},
        {"company": "Pleo",   "industry": "Fintech",  "country": "Denmark",        "employees": 900},
        {"company": "Figma",  "industry": "Design",   "country": "United States",  "employees": 1200},
        {"company": "SomeCo", "industry": "Retail",   "country": "Brazil",         "employees": 300},
    ]
    for c in test_companies:
        scored = score_company(c)
        print(f"{scored['company']:>8} | score {scored['icp_score']:>3} | tier {scored['tier']} | {scored['reason']}")

    # --- SHIP: score a batch and POST each to n8n ---
    N8N_WEBHOOK = "http://localhost:5678/webhook/lead-intake"
    sent, failed = 0, 0
    for company in test_companies:
        scored = score_company(company)
        print(f"Sending {scored['company']:>8} | score {scored['icp_score']:>3} | tier {scored['tier']} ...", end=" ")
        try:
            response = requests.post(N8N_WEBHOOK, json=scored)
            if response.ok:
                print(f"OK ({response.status_code})")
                sent += 1
            else:
                print(f"FAILED ({response.status_code})")
                failed += 1
        except requests.exceptions.RequestException as e:
            print(f"ERROR — {e}")
            failed += 1
        time.sleep(0.3)

    print(f"\nDone: {sent} sent, {failed} failed out of {len(test_companies)}.")