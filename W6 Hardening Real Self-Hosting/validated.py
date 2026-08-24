import requests
import json

URL = "http://localhost:11434/api/generate"
REQUIRED_KEYS = ["summary", "pain_point", "outreach_line"]


def build_prompt(company, industry):
    return f"""You are a B2B sales research assistant.
For the company below, return ONLY a JSON object with exactly these three keys:
- "summary": one sentence describing what the company likely does
- "pain_point": one operational pain point they probably face
- "outreach_line": one short, specific cold-email opening line

Company: {company}
Industry: {industry}"""


def call_model(prompt, model="llama3.2:3b"):
    """Send the prompt, return the raw response STRING (not parsed yet)."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }
    response = requests.post(URL, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["response"]


def validate(text):
    """Return a clean dict if the text passes all checks, else None."""
    # Check 1: does it even parse as JSON?
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None

    # Check 2: is it actually a dict (not a list or a number)?
    if not isinstance(data, dict):
        return None

    # Check 3: are all required keys present AND non-empty?
    for key in REQUIRED_KEYS:
        value = data.get(key, "")
        if not isinstance(value, str) or value.strip() == "":
            return None

    return data   # passed every check


def get_validated(company, industry, retries=2):
    """Call the model, validate, retry on failure, fall back if all attempts fail."""
    prompt = build_prompt(company, industry)

    for attempt in range(1, retries + 2):   # 1 first try + `retries` more
        try:
            text = call_model(prompt)
            result = validate(text)
            if result is not None:
                return result
            print(f"    [retry] attempt {attempt} for {company}: invalid output")
        except requests.exceptions.RequestException as e:
            print(f"    [retry] attempt {attempt} for {company}: request error {e}")

    # Every attempt failed -> safe fallback a human can spot
    print(f"    [FALLBACK] {company} flagged for review")
    return {
        "summary": "[NEEDS REVIEW]",
        "pain_point": "[NEEDS REVIEW]",
        "outreach_line": "[NEEDS REVIEW]",
    }


if __name__ == "__main__":
    # 1. A normal call — should succeed on the first try
    print("Real call:", get_validated("Stripe", "Financial Software"))
    print("-" * 50)

    # 2. Prove the validator rejects bad input, without needing the model to fail
    print("Good JSON:      ", validate('{"summary":"a","pain_point":"b","outreach_line":"c"}'))
    print("Missing a key:  ", validate('{"summary":"a"}'))
    print("Empty field:    ", validate('{"summary":"","pain_point":"b","outreach_line":"c"}'))
    print("Not JSON at all:", validate('Sure! Here you go: ...'))