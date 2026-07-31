import requests
import time

def fetch_post(post_id):
    url = f"https://jsonplaceholder.typicode.com/posts/{post_id}"
    response = requests.get(url)

    if not response.ok:
        return {"id": post_id, "ok": False, "reason": f"status {response.status_code}"}

    try:
        data = response.json()
    except ValueError:
        return {"id": post_id, "ok": False, "reason": "invalid JSON"}

    return {
        "id": post_id,
        "ok": True,
        "title": data.get("title", "NO TITLE"),
        "author": data.get("author", "NO AUTHOR"),
    }

# --- run over a batch of IDs ---
post_ids = [1, 2, 3, 9999]
results = []      # winners
failures = []     # rejects

for post_id in post_ids:
    print(f"Fetching post {post_id}...")
    record = fetch_post(post_id)

    if record["ok"]:
        results.append(record)
    else:
        failures.append(record)

    time.sleep(1)

# --- summary ---
print()
print(f"Batch complete: {len(results)} succeeded, {len(failures)} failed, {len(post_ids)} total")

print()
print("SUCCEEDED:")
for r in results:
    print(f"  Post {r['id']}: {r['title']}")

print()
print("FAILED (needs review):")
for f in failures:
    print(f"  Post {f['id']}: {f['reason']}")