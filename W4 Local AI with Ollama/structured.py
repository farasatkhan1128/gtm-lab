import requests
import json

def get_structured(company, industry, model="llama3.2:3b"):
    """Ask the model for structured JSON about a company. Returns a Python dict."""
    url = "http://localhost:11434/api/generate"

    prompt = f"""You are a B2B sales research assistant.
For the company below, return ONLY a JSON object with exactly these three keys:
- "summary": one sentence describing what the company likely does
- "pain_point": one operational pain point they probably face
- "outreach_line": one short, specific cold-email opening line

Company: {company}
Industry: {industry}"""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",        # force syntactically valid JSON
        "options": {
            "temperature": 0.2   # low = focused, consistent, repeatable
        }
    }

    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()

    # data["response"] is a JSON STRING — parse it into a real Python dict
    text = data["response"]
    result = json.loads(text)
    return result


if __name__ == "__main__":
    companies = [
        ("Bloom Health", "Healthcare"),
        ("Acme Robotics", "Manufacturing"),
        ("Nimbus Retail", "Retail"),
    ]

    for company, industry in companies:
        print("=" * 60)
        print(f"COMPANY: {company} ({industry})")
        result = get_structured(company, industry)
        print("  Summary:  ", result["summary"])
        print("  Pain:     ", result["pain_point"])
        print("  Outreach: ", result["outreach_line"])
    print("=" * 60)