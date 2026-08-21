# D:\gtm-lab\W5 Full Pipeline Integration\service.py
import sys, os, csv
sys.path.insert(0, r"D:\gtm-lab\W3 API handling and batch enrichment pipeline")
sys.path.insert(0, r"D:\gtm-lab\W4 Local AI with Ollama")

from flask import Flask, request, jsonify
from icp_score import score_company      # (company) -> ?  the run will show us
from validated import get_validated      # (company, industry) -> ?  the run will show us

app = Flask(__name__)

@app.post("/process")
def process():
    lead = request.get_json(force=True)

    # n8n may wrap the real lead under "body" — unwrap if so
    if "body" in lead and "company" not in lead:
        lead = lead["body"]

    score = score_company(lead)
    lead["icp_score"] = score.get("icp_score")
    lead["tier"] = score.get("tier")

    ai = get_validated(lead.get("company"), lead.get("industry"))   # dict: outreach_line, pain_point, summary
    lead["outreach_line"] = ai.get("outreach_line")
    lead["pain_point"] = ai.get("pain_point")
    lead["summary"] = ai.get("summary")

    lead["stage"] = "enriched"

    print("DEBUG /process out:", lead)
    return jsonify(lead), 200

@app.post("/commit")
def commit():
    lead = request.get_json(force=True)
    path = os.path.join(os.path.dirname(__file__), "pipeline_output.csv")
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lead.keys()))
        if not exists:
            w.writeheader()
        w.writerow(lead)
    return jsonify({"written": True}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)   # 0.0.0.0 so the Docker container can reach it