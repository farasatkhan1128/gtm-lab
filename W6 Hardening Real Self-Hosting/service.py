# D:\gtm-lab\W6 Hardening Real Self-Hosting\service.py
import sys, os, csv, json
from datetime import datetime

from flask import Flask, request, jsonify
from icp_score import score_company
from validated import get_validated

app = Flask(__name__)

WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN", "")

def check_token(req):
    token = req.headers.get("X-Webhook-Token", "")
    return token == WEBHOOK_TOKEN

LOG_PATH = os.path.join(os.path.dirname(__file__), "pipeline_runs.log")

def log_run(company, industry, score, tier, stage, status):
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "company": company,
        "industry": industry,
        "icp_score": score,
        "tier": tier,
        "stage": stage,
        "status": status,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

@app.post("/process")
def process():
    if not check_token(request):
        return jsonify({"error": "Unauthorised"}), 401
    lead = request.get_json(force=True)

    # n8n may wrap the real lead under "body" — unwrap if so
    if "body" in lead and "company" not in lead:
        lead = lead["body"]

    score = score_company(lead)
    lead["icp_score"] = score.get("icp_score")
    lead["tier"] = score.get("tier")

    ai = get_validated(lead.get("company"), lead.get("industry"))
    lead["outreach_line"] = ai.get("outreach_line")
    lead["pain_point"] = ai.get("pain_point")
    lead["summary"] = ai.get("summary")

    lead["stage"] = "enriched"

    log_run(
        lead.get("company", ""),
        lead.get("industry", ""),
        lead.get("icp_score", 0),
        lead.get("tier", ""),
        lead.get("stage", ""),
        "ok"
    )

    print("DEBUG /process out:", lead)
    return jsonify(lead), 200

@app.post("/commit")
def commit():
    lead = request.get_json(force=True)
    path = os.path.join(os.path.dirname(__file__), "pipeline_output.csv")

    # Idempotency check — skip if company already exists in CSV
    company = lead.get("company", "").strip().lower()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("company", "").strip().lower() == company:
                    log_run(
                        lead.get("company", ""),
                        lead.get("industry", ""),
                        lead.get("icp_score", 0),
                        lead.get("tier", ""),
                        lead.get("stage", ""),
                        "duplicate"
                    )
                    return jsonify({"written": False, "reason": "duplicate"}), 200

    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lead.keys()))
        if not exists:
            w.writeheader()
        w.writerow(lead)

    log_run(
        lead.get("company", ""),
        lead.get("industry", ""),
        lead.get("icp_score", 0),
        lead.get("tier", ""),
        lead.get("stage", ""),
        "committed"
    )
    return jsonify({"written": True}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)