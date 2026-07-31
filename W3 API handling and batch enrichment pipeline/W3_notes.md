# Week 3 — APIs & Batch Enrichment (Revision Notes)

**Goal of the week:** build a working enrichment pipeline in Python, one concept per day.
By Friday: take a list of inputs → call an API for each → handle failures gracefully →
pace the calls → split winners from rejects → write two clean CSV files to disk.

**Files built this week (in `W3/`):**
`api_test.py` · `safe_fetch.py` · `batch_fetch.py` · `write_results.py` · `enrich_companies.py`
plus outputs `posts_enriched.csv`, `posts_review.csv`, `companies_enriched.csv`, `companies_review.csv`.

**The one-line story of the week:** *A failed request never stops your script on its own — it hands
you back a response object, and it's on you to inspect it before you trust it. Everything else this
week is layers of "inspect before you trust" plus the plumbing to run that over a batch and save it.*

---

## The big idea: a failed request does NOT raise an error

When you run `requests.get(url)` you always get a **response object** back — even on a 404 or 500.
Python does not judge the response as good or bad; the status code is just *data inside* that object.
Your script only crashes later, when you treat a failed response as if it held valid data
(e.g. parsing an error page, or reaching for a field that isn't there).

That is why the whole week is about **checking things before using them**.

---

## Monday — Live API calls

- `requests.get(url)` makes a live call and returns a response object.
- `response.status_code` → the HTTP result: **200** = success, **404** = not found, etc.
- **GET** = "give me data" (read). **POST** = "here is data, do something with it" (create/send).
- A 404 prints its status and the script keeps running — it does not stop by itself.

---

## Tuesday — Handling responses safely (`safe_fetch.py`)

**Three independent defensive layers, each catching a different failure:**

| Layer | Catches | Tool |
|---|---|---|
| 1. Status check | Bad *envelope* — 404, 500, timeout | `response.ok` (or `status_code == 200`) |
| 2. Parse guard | Good status but *unparseable body* (HTML/empty instead of JSON) | `try / except ValueError` around `.json()` |
| 3. Field fallback | Parsed fine but a *field is missing* (even on a 200) | `.get(key, fallback)` |

**Key distinctions to remember:**

- `response.ok` is `True` for any status **under 400** (all 2xx/3xx), `False` for 4xx/5xx.
  More robust than `status_code == 200` because it also accepts 201, 204, etc.
- `data['email']` raises **`KeyError`** if `email` is missing.
  `data.get('email', 'N/A')` returns the fallback `'N/A'` instead — no crash.
- `.json()` itself can crash if the body isn't valid JSON → raises `JSONDecodeError`,
  which is a kind of **`ValueError`**, so `except ValueError` catches it.
- **`raise_for_status()`** — the opposite of "skip quietly": it deliberately raises on a 4xx/5xx
  so the script stops *loudly*. Use it when a call **must** succeed (e.g. downloading required data)
  and a failure means nothing downstream can work.

**Guard-clause structure** — check the bad cases first and `return` early, then do the real work
flat at the bottom. Flatter and easier to read than deep nesting.

```python
import requests

def fetch_post(post_id):
    url = f"https://jsonplaceholder.typicode.com/posts/{post_id}"
    response = requests.get(url)
    print(f"Post {post_id} -> status {response.status_code}")

    if not response.ok:                       # 1. bad envelope -> bail
        print(f"  Skipping — bad response, moving on")
        return

    try:                                      # 3. guard the parse itself
        data = response.json()
    except ValueError:
        print("  Response wasn't valid JSON — skipping")
        return

    title = data.get('title', 'NO TITLE')     # 3. missing-field fallback
    author = data.get('author', 'NO AUTHOR')
    print(f"  Title: {title}")
    print(f"  Author: {author}")

fetch_post(1)
fetch_post(9999)
```

---

## Wednesday — Batch calls (`batch_fetch.py`)

**Three parts:**

1. **Return, don't print.** A batch function must **`return`** a structured result so the loop can
   *collect* it. Printing just displays it and throws it away — nothing to save, score, or write.
2. **Pace the calls.** Add `time.sleep()` between calls to avoid **429 Too Many Requests**
   (the server rejecting you for going too fast). The sleep is a *dial*, tuned to the API's limit —
   too short = throttled, too long = the job crawls.
3. **Split into two streams.** Tag each returned record with an `"ok"` flag; the loop routes
   `True` → `results`, `False` → `failures` (with a `reason`). Never silently drop a failure.

**Key points:**

- `results = []` and `failures = []` are created **before** the loop. If created *inside* it,
  they'd reset every iteration and only the last item would survive.
- `if record["ok"]:` reads the record's own verdict — cleaner and more informative than `is not None`.
- Returning `{"ok": False, "reason": ...}` instead of a bare `None` means you know *why* it failed,
  so you can log, review, or **retry** the specific failures.

```python
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
        "id": post_id, "ok": True,
        "title": data.get("title", "NO TITLE"),
        "author": data.get("author", "NO AUTHOR"),
    }

post_ids = [1, 2, 3, 9999]
results, failures = [], []

for post_id in post_ids:
    print(f"Fetching post {post_id}...")
    record = fetch_post(post_id)
    if record["ok"]:
        results.append(record)
    else:
        failures.append(record)
    time.sleep(1)                 # pace the calls -> avoid 429

print(f"\nBatch complete: {len(results)} succeeded, {len(failures)} failed, {len(post_ids)} total")
```

---

## Thursday — Writing results to CSV (`write_results.py`)

**The persistence step.** A list of dicts in memory vanishes when the script ends. Writing it to a
CSV makes it a real, openable, shareable file.

**Tools:**

- `csv.DictWriter(f, fieldnames=...)` — purpose-built for writing a list of dictionaries.
- `writeheader()` — writes the top row (the column names).
- `writerows(list)` — writes one row per dict, matching each dict's keys to the fieldnames.

**Gotchas / habits:**

- Open in **`"w"` (write) mode** → creates the file, or **overwrites** it completely on each run.
  (Run twice, you still get 3 rows, not 6.) Append mode is **`"a"`** — adds without erasing.
- **`newline=""`** in `open()` — prevents the **Windows** double-line-ending bug that puts a blank
  line between every data row. Always include it for CSV writing.
- **Fieldnames must match the dict's keys.** Successes and failures have different shapes, so they
  go to **different files** with **different fieldnames** (`posts_enriched.csv` vs `posts_review.csv`).
- **DRY (Don't Repeat Yourself):** two near-identical write blocks → one reusable `write_csv()`
  function called twice. One place to fix bugs, one place to change behaviour.
- **Empty-list guard:** report "header only — no rows" instead of silently producing a header-only
  file that looks broken.

```python
import csv

def write_csv(filename, rows, fieldnames):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    if len(rows) == 0:
        print(f"  {filename}: header only — no rows to write")
    else:
        print(f"  Wrote {len(rows)} rows to {filename}")

write_csv("posts_enriched.csv", results, ["id", "ok", "title", "author"])
write_csv("posts_review.csv",  failures, ["id", "ok", "reason"])
```

---

## Friday — Full pipeline on company data (`enrich_companies.py`)

**Consolidation day.** No new concepts — assemble the whole thing (fetch → handle → pace → split →
write) on **company-shaped nested data**, the shape a real enrichment API (Apollo/Clearbit) returns.

**The one real new technique: chained `.get()` for nested data.**

```python
record.get("location", {}).get("city", "UNKNOWN")
```

Read it as: get `location` (or an empty `{}` if missing), then get `city` out of that (or `"UNKNOWN"`
if missing). This safely digs into nested objects without a `KeyError` when a level is absent —
exactly how you'd pull `employee_count` or a specific email out of a real Apollo record that doesn't
always have every field.

**The API-deprecation war story (the most transferable lesson of the week):**
The planned live API (`restcountries.com/v3.1`) had been **deprecated** — it returned an error dict
instead of data, so `data[0]` crashed with `KeyError: 0` (a *dict* being indexed like a list).
v5 now needs an API key; a keyless alternative endpoint also missed. The disciplined debugging loop:

> **crash → inspect the *real* response (`print(type(data))`, `print(data)`) → adjust to fit → rerun**

For a consolidation day, we swapped the live call for a **local dataset** (`COMPANY_DB`) that returns
the same nested shape — isolating the pipeline skill from flaky endpoints. The **swap-point comment**
marks where a real Apollo call would slot back in.

**What would change to make it real (the swap point):**
Replace the local `COMPANY_DB.get(domain)` lookup with `requests.get(...)` to the Apollo endpoint,
plus an **auth header/API key**, status handling, JSON parsing, and rate limiting. The loop, split,
pacing, and fallbacks stay identical.

```python
import time
import csv

COMPANY_DB = {
    "stripe.com": {"name": "Stripe", "industry": "Financial Software",
                   "location": {"city": "San Francisco", "country": "United States"}, "employees": 8000},
    "monzo.com":  {"name": "Monzo", "industry": "Banking",
                   "location": {"city": "London", "country": "United Kingdom"}},   # no 'employees'
    "canva.com":  {"name": "Canva", "industry": "Design Software",
                   "location": {"city": "Sydney"}, "employees": 4000},             # no 'country'
}

def enrich_company(domain):
    # --- swap point: in production this is an Apollo/Clearbit GET by domain + API key ---
    record = COMPANY_DB.get(domain)
    if record is None:                                    # local twin of a 404 / no-match
        return {"input": domain, "ok": False, "reason": "no match found"}
    return {
        "input": domain, "ok": True,
        "company":   record.get("name", "UNKNOWN"),
        "industry":  record.get("industry", "UNKNOWN"),
        "city":      record.get("location", {}).get("city", "UNKNOWN"),      # nested .get()
        "country":   record.get("location", {}).get("country", "UNKNOWN"),   # nested .get()
        "employees": record.get("employees", 0),
    }

def write_csv(filename, rows, fieldnames):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    if len(rows) == 0:
        print(f"  {filename}: header only — no rows to write")
    else:
        print(f"  Wrote {len(rows)} rows to {filename}")

inputs = ["stripe.com", "monzo.com", "canva.com", "notacompany.xyz"]
results, failures = [], []

for domain in inputs:
    print(f"Enriching {domain}...")
    record = enrich_company(domain)
    if record["ok"]:
        results.append(record)
    else:
        failures.append(record)
    time.sleep(0.3)               # habit; in production this paces real API calls

print(f"\nEnrichment complete: {len(results)} succeeded, {len(failures)} failed, {len(inputs)} total")

write_csv("companies_enriched.csv", results,
          ["input", "ok", "company", "industry", "city", "country", "employees"])
write_csv("companies_review.csv", failures, ["input", "ok", "reason"])
```

**Result — `companies_enriched.csv` (fallbacks landed in the file):**
```
input,ok,company,industry,city,country,employees
stripe.com,True,Stripe,Financial Software,San Francisco,United States,8000
monzo.com,True,Monzo,Banking,London,United Kingdom,0          <- missing employees -> 0
canva.com,True,Canva,Design Software,Sydney,UNKNOWN,4000      <- missing country  -> UNKNOWN
```

---

## Glossary (every term used this week)

- **API** — a service you call over the internet to get or send data.
- **`requests`** — the Python library for making HTTP calls (`requests.get`, `requests.post`).
- **Response object** — what `requests.get()` returns; holds the status code and body. Always
  returned, even on failure — it does not raise by itself.
- **Status code** — the HTTP result. 200 OK, 201 Created, 204 No Content, 404 Not Found,
  429 Too Many Requests, 500 Server Error.
- **`response.ok`** — `True` for any status under 400; a robust "did it succeed?" check.
- **`response.status_code`** — the raw number (e.g. 200, 404).
- **`raise_for_status()`** — deliberately raises an error on a 4xx/5xx (loud failure on demand).
- **`.json()`** — parses the response body from JSON text into a Python dict/list. Can raise
  `JSONDecodeError` if the body isn't valid JSON.
- **GET / POST** — GET reads data; POST sends/creates data.
- **`KeyError`** — raised when you ask a **dict** for a key it doesn't have (`data['missing']`).
- **`IndexError`** — raised when you ask a **list** for a position that doesn't exist (`data[99]`).
- **`ValueError`** — a broad error type; `JSONDecodeError` is a kind of `ValueError`.
- **`.get(key, fallback)`** — safe dict access: returns the value, or the fallback if the key is
  missing, instead of crashing.
- **`try / except`** — attempt risky code; if it raises the named error, run the `except` block
  instead of crashing.
- **`return`** — hands a value back from a function to the caller (so a loop can collect it).
  Also used to bail out of a function early.
- **`"ok"` flag** — a boolean field on each record marking success/failure, used to route it.
- **`time.sleep(seconds)`** — pauses the program; used to pace API calls.
- **429 / rate limit** — the server rejecting calls made too fast; fixed by pacing with `sleep`.
- **`csv.DictWriter`** — writes a list of dicts to a CSV; needs `fieldnames`.
- **`writeheader()` / `writerows()`** — write the column-name row / all the data rows.
- **`"w"` / `"a"` mode** — write (overwrite) / append (add without erasing).
- **`newline=""`** — stops the Windows blank-line-between-rows CSV bug.
- **`fieldnames`** — the ordered list of column names; must match the dict's keys.
- **`with open(...) as f:`** — opens a file and auto-closes it when the block ends.
- **Guard clause** — check bad cases up front and `return` early; keeps the main logic flat.
- **DRY** — "Don't Repeat Yourself"; pull repeated code into one reusable function.
- **Nested `.get()` chain** — `x.get("a", {}).get("b", default)`; safely digs into nested dicts.
- **Deprecated API** — a retired API version that stops returning real data; you migrate to a
  new endpoint (a normal, recurring event in real GTM work).

---

## Quizzes (with answers)

### Tuesday quiz — 6/6
1. **500 from a down server — does Python raise on that line?** No. You get a response object with
   `status_code = 500`; it doesn't raise by itself.
2. **`data['email']` vs `data.get('email')` when `email` is missing?** Brackets raise `KeyError`;
   `.get()` returns `None` (or a default if provided).
3. **`data.get('phone', 'no phone')` when `phone` is missing?** Returns `"no phone"`.
4. **What does `response.ok` give you over `status_code == 200`?** A simple True/False for success
   (status under 400), instead of matching one exact code.
5. **200, but `data = response.json()` still crashes — what and which guard?** Invalid JSON; caught by
   `try/except` around `.json()`.
6. **When use `raise_for_status()` to crash on purpose?** When the request *must* succeed (e.g.
   downloading required data), so it stops immediately on a server error.

### Wednesday quiz — 6/6
1. **Why return a dict instead of print in a batch?** Returning lets the loop collect and reuse the
   data; printing only displays it.
2. **What if `results = []` is inside the loop?** It resets every iteration, so only the last result
   is kept.
3. **What is 429 and the one-line fix?** Too Many Requests (rate-limited); add `time.sleep(1)`.
4. **Roughly how long does a 4-ID batch take with `sleep(1)`?** ~4 seconds — one sleep per call.
5. **What does the `"reason"` field give you over `None`?** Why it failed, so you can log, review, or
   retry specific failures.
6. **500 Apollo enrich, 60 no-match — what does Part C hand you?** Two structured lists: successes and
   failures-with-reasons — reviewable/retryable, not just printed and skipped.

### Thursday quiz — 6/6
1. **Why not 9–12 rows after multiple runs?** `"w"` overwrites the file at the start of each run.
2. **`writeheader()` vs `writerows()`?** Writes the column names / writes all the data rows.
3. **What does `newline=""` prevent, and on which OS?** Blank lines between rows, on Windows.
4. **Why can't two differently-shaped files share fieldnames?** Their rows have different keys, so each
   file needs matching fieldnames.
5. **One benefit of `write_csv()` over copy-paste?** Update the logic in one place only (DRY).
6. **Empty `failures` — what does the guard report and why useful?** "Header only — no rows"; clearer
   than silently leaving a header-only file that looks like a bug. (Note: the file *is* still created.)

### Week 3 wrap-up quiz — 10/10
1. **404 back — does Python raise on that line? What do you hold?** No; a response object with
   `status_code == 404`.
2. **Three defensive layers and what each catches?** Status check → HTTP errors; `try/except` on
   `.json()` → invalid JSON; `.get()` → missing dict fields.
3. **`data['email']` vs `data.get('email', 'N/A')` when missing?** `KeyError` vs returns `"N/A"`.
4. **Why `return` not `print()` in a batch function?** `return` gives the result to the loop to store
   and process; `print()` only displays it.
5. **What is 429 and the one line to avoid it?** Too many requests; add `time.sleep(1)`.
6. **What does the loop do with the `"ok"` flag?** Sends `True` records to `results`, `False` to
   `failures`.
7. **`"w"` mode on re-run?** Erases the existing file before writing new contents.
8. **Why can't `posts_enriched.csv` and `posts_review.csv` share fieldnames?** Different keys per row,
   so each needs matching fieldnames.
9. **Canva → `Sydney, UNKNOWN` without crashing — technique and why it matters?** `.get()` with
   fallbacks replaces missing values; real Apollo records often have incomplete fields.
10. **Which line marks where a real Apollo call slots in, and what changes?** The local lookup line;
    replace it with `requests.get(...)` plus auth, status handling, JSON parsing, and rate limiting.

---

## Interview framing (bank this)

> *"I built a batch enrichment pipeline in Python — it takes a list of company domains, calls an
> enrichment API for each with graceful handling of failures and missing fields, paces the calls to
> respect rate limits, and outputs a clean enriched file plus a review file of records that need
> attention."*

Every clause is something you did and understand line by line.

**Core habit of the week:** *never silently drop a failure — route it somewhere reviewable, with a
reason.*

---

## What's next — Week 4

**pandas** — the library that turns row-by-row CSV work into fast table operations (filter, sort,
group, merge). It sits under every serious GTM data workflow and will supercharge both Week 2's
`clean_leads.py` and this week's enrichment output.
