import requests

def ask_ollama(prompt, model="llama3.2:3b"):
    """Send a prompt to the local Ollama model and return just the text answer."""
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()          # trip an error on a bad HTTP status
        data = response.json()
        return data["response"].strip()      # hand back only the answer text
    except requests.exceptions.RequestException as e:
        return f"[ERROR] Request failed: {e}"


# --- Try it out with a few different prompts ---
if __name__ == "__main__":
    q1 = ask_ollama("In one sentence, what is a common pain point for a small healthcare company?")
    print("Q1:", q1)
    print("-----")

    q2 = ask_ollama("Write a one-line cold email opener for a company called Acme Robotics in manufacturing.")
    print("Q2:", q2)