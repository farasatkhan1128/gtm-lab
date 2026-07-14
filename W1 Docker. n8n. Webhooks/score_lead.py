# A lead, same shape as the n8n webhook data
lead = {
    "company_name": "Glow Beauty London",
    "domain": "glowbeauty.co.uk",
    "industry": "Beauty",
    "country": "United Kingdom",
    "employees": 45
}

def score_lead(lead):
    score = 0
    reasons = []

    # Rule 1: UK markeet (worth 25)
    if lead["country"] == "United Kingdom":
        score += 25
        reasons.append("UK market")

    # Rule 2: target industry (worth 30)
    if lead["industry"] == "Beauty":
        score += 30
        reasons.append("target industry (beauty)")

    # Rule 3: right team size (worth 30)
    if lead["employees"] >= 20:
        score += 30
        reasons.append("suitable team size")


    # Turn the number into a tier
    if score >= 80:
        tier = "Tier 1"
    elif score >= 50:
        tier = "Tier 2"
    else:
        tier = "Tier 3"

    # Join the reasons into one sentence
    reason = ", ".join(reasons)

    return {
        "icp_score": score,
        "tier": tier,
        "reason": reason 
    }
lead = {
    "company_name": "Glow Beauty London",
    "domain": "glowbeauty.co.uk",
    "industry": "Beauty",
    "country": "United Kingdom",
    "employees": 45
}

print(score_lead(lead))
weak_lead = {
    "company_name": "Tiny Tools Ltd",
    "domain": "tinytools.com",
    "industry": "Manufacturing",
    "country": "Germany",
    "employees": 5
}

print(score_lead(weak_lead))