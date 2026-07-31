import csv

# --- the two streams Wednesday's batch produced (hardcoded to focus on writing) ---
results = [
    {"id": 1, "ok": True, "title": "sunt aut facere", "author": "NO AUTHOR"},
    {"id": 2, "ok": True, "title": "qui est esse", "author": "NO AUTHOR"},
    {"id": 3, "ok": True, "title": "ea molestias quasi", "author": "NO AUTHOR"},
]

failures = [
    {"id": 9999, "ok": False, "reason": "status 404"},
]

def write_csv(filename, rows, fieldnames):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    if len(rows) == 0:
        print(f"  {filename}: header only — no rows to write")
    else:
        print(f"  Wrote {len(rows)} rows to {filename}")

# --- write both streams ---
print("Writing output files:")
write_csv("posts_enriched.csv", results, ["id", "ok", "title", "author"])
write_csv("posts_review.csv", failures, ["id", "ok", "reason"])