# Week 3 — APIs, Batch Enrichment & the Weighted ICP Scorer (Revision Notes)

**Goal of the week:** build a working enrichment + scoring pipeline in Python, one concept per day —
then push scored accounts into n8n. By the end: take a list of inputs → call an API for each →
handle failures gracefully → pace the calls → page through everything → shape it in pandas →
score each company against a defensible ICP → POST the scored records into n8n.

**Files built (in `W3/`):**
`api_test.py` · `safe_fetch.py` · `batch_fetch.py` · `write_results.py` · `enrich_companies.py` ·
`pagination.py` · `pandas_basics.py` · `icp_score.py`
Outputs: `posts_enriched.csv`, `posts_review.csv`, `companies_enriched.csv`, `companies_review.csv`.

**The one-line story of the week:** *A failed request never stops your script on its own — it hands
you back a response object, and it's on you to inspect it before you trust it.* Everything else is
layers of "inspect before you trust", the plumbing to run that over a batch, and then scoring + shipping.

---

# PART 1 — APIs & Batch Enrichment

## The big idea: a failed request does NOT raise an error

`requests.get(url)` always returns a **response object** — even on a 404 or 500. Python doesn't judge
the response; the status code is just *data inside* it. Your script only crashes later, when you treat
a failed response as valid (parsing an error page, or reaching for a field that isn't there). That's
why the whole week is about **checking things before using them.**

## Monday — Live API calls
- `requests.get(url)` makes a live call, returns a response object.
- `response.status_code` → **200** success, **404** not found, etc.
- **GET** = read data. **POST** = send/create data.
- A 404 prints its status and the script keeps running — it does not stop by itself.

## Tuesday — Handling responses safely (`safe_fetch.py`)

**Three independent defensive layers, each catching a different failure:**

| Layer | Catches | Tool |
|---|---|---|
| 1. Status check | Bad *envelope* — 404, 500, timeout | `response.ok` (or `status_code == 200`) |
| 2. Parse guard | Good status but *unparseable body* | `try / except ValueError` around `.json()` |
| 3. Field fallback | Parsed fine but a *field is missing* | `.get(key, fallback)` |

**Key distinctions:**
- `response.ok` is `True` for any status **under 400** (all 2xx/3xx) — more robust than `== 200`
  because it also accepts 201, 204, etc.
- `data['email']` raises **`KeyError`** if missing; `data.get('email', 'N/A')` returns the fallback.
- `.json()` can crash on a non-JSON body → **`JSONDecodeError`**, which is a **`ValueError`**, so
  `except ValueError` catches it.
- **`raise_for_status()`** — deliberately raises on 4xx/5xx (loud failure). Use when a call *must*
  succeed and a failure means nothing downstream can work.
- **Guard clauses:** check bad cases first and `return` early, real work flat at the bottom.

```python
import requests

def fetch_post(post_id):
    url = f"https://jsonplaceholder.typicode.com/posts/{post_id}"
    response = requests.get(url)
    if not response.ok:                       # 1. bad envelope -> bail
        return None
    try:                                      # 2. guard the parse
        data = response.json()
    except ValueError:
        return None
    title = data.get('title', 'NO TITLE')     # 3. missing-field fallback
    return title
```

## Wednesday — Batch calls (`batch_fetch.py`)

1. **Return, don't print** — a batch function must `return` a structured result so the loop can
   *collect* it. Printing throws it away.
2. **Pace the calls** — `time.sleep()` between calls to avoid **429 Too Many Requests**. The sleep is a
   dial tuned to the API's limit (too short = throttled, too long = job crawls).
3. **Split into two streams** — tag each record with an `"ok"` flag; loop routes `True` → `results`,
   `False` → `failures` (with a `reason`). Never silently drop a failure.

- `results = []` / `failures = []` go **before** the loop (inside, they'd reset each iteration).
- `if record["ok"]:` reads the record's own verdict — cleaner than `is not None`.
- Returning `{"ok": False, "reason": ...}` (not bare `None`) means you know *why* it failed → log,
  review, or **retry**.

## Thursday — Writing results to CSV (`write_results.py`)

The **persistence** step — a list of dicts vanishes when the script ends; a CSV is a real file.

- `csv.DictWriter(f, fieldnames=...)` + `writeheader()` + `writerows(list)`.
- Open in **`"w"` (write) mode** → creates or **overwrites** the file each run (run twice, still 3 rows,
  not 6). Append mode is **`"a"`** (adds without erasing).
- **`newline=""`** in `open()` — prevents the **Windows** blank-line-between-rows bug. Always include it.
- **Fieldnames must match the dict's keys.** Successes and failures have different shapes → different
  files (`posts_enriched.csv` vs `posts_review.csv`) with different fieldnames.
- **DRY:** two near-identical write blocks → one reusable `write_csv()` function.
- **Empty-list guard:** report "header only — no rows" instead of a silent header-only file.

```python
import csv
def write_csv(filename, rows, fieldnames):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {filename}: header only — no rows" if len(rows)==0 else f"  Wrote {len(rows)} rows to {filename}")
```

## Friday — Full pipeline on company data (`enrich_companies.py`)

Consolidation: assemble fetch → handle → pace → split → write on **company-shaped nested data**.

**New technique — chained `.get()` for nested data:**
```python
record.get("location", {}).get("city", "UNKNOWN")
```
Get `location` (or `{}` if missing), then `city` out of that (or `"UNKNOWN"`). Digs into nested objects
without a `KeyError` — exactly how you'd pull `employee_count` or an email from a real Apollo record.

**API-deprecation war story (most transferable lesson):** the planned live API (`restcountries.com/v3.1`)
was **deprecated** — returned an error dict, so `data[0]` crashed with `KeyError: 0` (a *dict* indexed
like a list). v5 now needs a key; a keyless alternative also missed. Debugging loop:
> **crash → inspect the real response (`print(type(data))`, `print(data)`) → adjust → rerun**

For a consolidation day we swapped the live call for a **local dataset** (same nested shape). The
**swap-point comment** marks where a real Apollo call (URL + auth header + status/JSON handling +
rate limiting) would slot back in — the loop, split, pacing, and fallbacks stay identical.

Result lands `companies_enriched.csv` + `companies_review.csv`; fallbacks (`0`, `UNKNOWN`) persist to disk.

---

# PART 2 — Pandas & the Weighted ICP Scorer

## Pagination — getting ALL the data (`pagination.py`)

APIs hand back large results in **pages**. Read only page 1 and you silently miss the rest — a dangerous
enrichment bug (nothing crashes).

```python
all_rows = []
page = 1
while True:                              # open-ended: page count unknown upfront
    response = get_page(page)            # prod: requests.get(url, params={"page": page})
    all_rows.extend(response["rows"])    # .extend adds every row into the master list
    if not response["has_more"]:         # STOP CONDITION — the load-bearing line
        break
    page += 1
    time.sleep(0.3)
```
- **`while True`** is deliberately infinite; **`break`** is the *only* exit. Remove the stop condition →
  loops forever (hammers a real server).
- **`.extend()`** unpacks a page's list; `.append()` would nest it as one item (wrong here).
- Two styles: **page-number** (`?page=1,2,3…`) and **cursor/offset** (token points to next batch —
  Apollo). Same loop shape.

## Pandas — working with tables (`pandas_basics.py`)

Manipulate a whole table at once, no row loops. `import pandas as pd`.
Install: `pip install pandas` (or `python -m pip install pandas`).

**GOTCHA (cost real time):** multiple Python versions → pandas installs in one, VS Code ▶ runs another →
`ModuleNotFoundError`. Fix: `Ctrl+Shift+P` → **Python: Select Interpreter** → pick the one with pandas.
Long-term fix = a **virtual environment** per project.

### DataFrame — a table in Python
`pd.DataFrame(list_of_dicts)` → each dict a row, each key a column.

**Inspect any new dataset first:**
```python
df                    # whole table (auto-indexed)
df.head(3)            # first 3 rows
df.shape              # (rows, columns)
df.columns.tolist()   # column names
df.describe()         # count/mean/std/min/quartiles/max on NUMBER columns
```
`.describe()` quartiles (25/50/75%) show natural cut-points — evidence for *where to band*.

### Filtering — keep rows matching a condition
```python
df[df["employees"] >= 3000]                                    # inner = boolean mask; df[...] keeps Trues
df[df["industry"] == "Fintech"]                                # text filter, ==
df[(df["industry"] == "Fintech") & (df["employees"] >= 2000)]  # TWO conditions
len(df[df["country"] == "United States"])                      # len() to COUNT
```
**Two-condition rule:** use **`&`** (not `and`), wrap **each** condition in its own `( )`.

### Grouping — collapse rows into per-category summaries
```python
df.groupby("industry").size()                # count per group
df.groupby("industry")["employees"].mean()   # average a column per group
df.groupby("country")["employees"].sum()     # total a column per group
```
Pattern: `df.groupby("SPLIT_BY")["MEASURE"].AGGREGATE()` (`size`/`mean`/`sum`/`max`/`min`).

## The Weighted ICP Scorer (`icp_score.py`)

**ICP score** = how well a company matches your Ideal Customer Profile → **score (0–100)**, **tier
(A/B/C)**, **reason**. Sales works A-tier first.

**The bar: you can defend EVERY weight.** Weights come from the ICP (imaginary: *a payments/financial-ops
tool selling best to mid-to-large fintech & software in core English-speaking markets*).

### Banding — number → category (check highest threshold first)
```python
def size_band(employees):
    if employees >= 5000:   return "Enterprise"
    elif employees >= 1000: return "Mid-market"   # already ruled out 5000+, so 1000–4999
    else:                   return "Startup"
```
Test the boundaries (5000, 999, 1000) — where banding bugs hide.

### The three scorers (return points)
```python
def industry_points(industry):          # strongest signal (0–40)
    if industry == "Fintech":            return 40
    elif industry in ("HR Software", "Software"): return 30
    elif industry == "Design":           return 15
    else:                                return 5

def country_points(country):            # where we can sell (0–30)
    if country in ("United States", "United Kingdom"): return 30
    elif country in ("Australia", "Denmark", "Canada", "Germany", "Ireland"): return 15
    else:                                return 5

def size_points(employees):             # budget/seats (0–30)
    band = size_band(employees)          # REUSES size_band — one source of truth
    if band == "Enterprise":  return 30
    elif band == "Mid-market": return 25
    else:                      return 10
```
- **`in (tuple)`** = "is it any of these?" — cleaner than chained `or`.
- **`size_points` reuses `size_band`** → change the Enterprise cutoff in one place (DRY).
- **`else` = floor score** → unknown industry/country scores low, never crashes. Every company gets a score.

### Assemble
```python
def score_company(company):
    ind_pts  = industry_points(company["industry"])
    ctry_pts = country_points(company["country"])
    sz_pts   = size_points(company["employees"])
    total = ind_pts + ctry_pts + sz_pts
    if total >= 80:   tier = "A"
    elif total >= 60: tier = "B"
    else:             tier = "C"
    band = size_band(company["employees"])
    reason = (f"{company['industry']} ({ind_pts}) + "
              f"{company['country']} ({ctry_pts}) + "
              f"{band} ({sz_pts}) = {total}")
    return {**company, "icp_score": total, "tier": tier, "reason": reason}
```
- **`{**company, ...}`** — dictionary unpacking; keep original fields, ADD new ones (enrichment).
- **The `reason` string** is "defend every weight" made literal — carries the full arithmetic.

**Worked results:**
```
Stripe | 100 | A | Fintech (40) + United States (30) + Enterprise (30) = 100   drop everything
Pleo   |  65 | B | Fintech (40) + Denmark (15) + Startup (10) = 65             great industry, weak geo/size
Figma  |  70 | B | Design (15) + United States (30) + Mid-market (25) = 70     good co, weak industry
SomeCo |  20 | C | Retail (5) + Brazil (5) + Startup (10) = 20                 poor everywhere
```
Pleo & Figma both B — for *opposite* reasons; the reason string surfaces that.

## Shipping — POST scored accounts into n8n

First **POST** of the week (all week was GET). POST *sends* data.
```python
response = requests.post(N8N_WEBHOOK, json=scored)   # json= auto-converts dict + sets JSON header
```
Batch send reuses the whole toolkit: batch loop + `sleep` (Wed), `response.ok` + `try/except` (Tue),
sent/failed counter (Thu).

**n8n webhook — test vs production (key operational lesson):**
- **Test URL** (`/webhook-test/lead-intake`): catches **ONE** request after "Listen for test event";
  shows data live in the editor. Send 4 → only the first lands, rest 404.
- **Production URL** (`/webhook/lead-intake`): listens **continuously** — but ONLY while the workflow is
  **Published/Active**. Not published → every POST **404**, however correct the URL. (This cost a run.)
- In this n8n build, **"Published"** (green dot) = active; there was no separate "Activate" toggle.

**Result:** workflow Published + URL swapped to `/webhook/` → `4 sent, 0 failed`, four production
executions. Python out → n8n in → loop closed.

---

## Glossary

- **Response object** — what `requests.get/post` returns; holds status + body. Always returned, even on failure.
- **Status code** — 200 OK, 201 Created, 204 No Content, 404 Not Found, 429 Too Many Requests, 500 Server Error.
- **`response.ok`** — True for any status under 400.
- **`raise_for_status()`** — raises on 4xx/5xx (loud failure on demand).
- **`.json()`** — parse body to dict/list; can raise `JSONDecodeError` (a `ValueError`).
- **GET / POST** — read / send data.
- **`KeyError` / `IndexError` / `ValueError`** — missing dict key / missing list position / broad value error.
- **`.get(key, fallback)`** — safe dict access with a default.
- **`try / except`** — attempt risky code; run `except` on the named error instead of crashing.
- **`"ok"` flag** — boolean field marking success/failure, used to route records.
- **`time.sleep(s)` / 429** — pause between calls / "too many requests" rejection.
- **`csv.DictWriter` / `writeheader` / `writerows`** — write dicts to CSV.
- **`"w"` / `"a"`** — write (overwrite) / append.
- **`newline=""`** — stops the Windows blank-line CSV bug.
- **`with open(...) as f:`** — opens and auto-closes a file.
- **Guard clause** — check bad cases up front and `return` early.
- **DRY** — Don't Repeat Yourself; one reusable function.
- **Chained `.get()`** — `x.get("a", {}).get("b", default)`; safe nested access.
- **Deprecated API** — a retired version that stops returning data; you migrate endpoints.
- **Pagination / `while True` / `break`** — retrieve results in pages; break is the only exit.
- **`.extend()` vs `.append()`** — extend adds every item; append adds the list as one item.
- **DataFrame / `pd.DataFrame(...)`** — a table (rows × named columns) from a list of dicts.
- **`.head` / `.shape` / `.describe` / `.columns`** — inspect a DataFrame.
- **Boolean mask** — True/False per row; `df[mask]` keeps the Trues.
- **`&` filter rule** — join conditions with `&`, each in `( )`; not `and`.
- **`groupby`** — split by category, then aggregate.
- **Banding** — map a number to a category; check high threshold first.
- **ICP score / tier / reason** — fit score, A/B/C bucket, human-readable breakdown.
- **`in (tuple)`** — membership test; cleaner than chained `or`.
- **`{**dict, ...}`** — dictionary unpacking (enrichment: keep + add fields).
- **`requests.post(url, json=d)`** — send dict as JSON body; header auto-set.
- **Test vs production webhook** — dev endpoint (catches one) vs live endpoint (continuous, only while Published).

---

## Quizzes (with answers)

### Tuesday — 6/6
1. 500 from a down server, does Python raise on that line? **No — response object with `status_code=500`.**
2. `data['email']` vs `data.get('email')` when missing? **`KeyError` vs `None`/default.**
3. `data.get('phone', 'no phone')` when missing? **`"no phone"`.**
4. `response.ok` over `== 200`? **True/False for any success (under 400).**
5. 200 but `.json()` crashes — what/which guard? **Invalid JSON; `try/except` around `.json()`.**
6. When `raise_for_status()`? **When the call must succeed, so it stops loudly on error.**

### Wednesday — 6/6
1. Why return not print in a batch? **Returning lets the loop collect/reuse; print only displays.**
2. `results=[]` inside the loop? **Resets each iteration, only last kept.**
3. What is 429, fix? **Too many requests; `time.sleep(1)`.**
4. Time for a 4-ID batch with `sleep(1)`? **~4s, one sleep per call.**
5. `"reason"` over `None`? **Why it failed → log/review/retry.**
6. 500 enrich, 60 no-match — what does the split hand you? **Two lists: successes + failures-with-reasons.**

### Thursday — 6/6
1. Why not 9–12 rows after re-runs? **`"w"` overwrites each run.**
2. `writeheader()` vs `writerows()`? **Column names / all data rows.**
3. `newline=""` prevents what, which OS? **Blank lines between rows, Windows.**
4. Why can't two shapes share fieldnames? **Different keys; each needs matching fieldnames.**
5. `write_csv()` over copy-paste? **Update logic in one place (DRY).**
6. Empty list — what does the guard report? **"Header only — no rows" (file still created).**

### Week 3 (Part 1) wrap-up — 10/10
1. 404 back — raise? what do you hold? **No; response object, `status_code==404`.**
2. Three defensive layers? **Status check / `try-except` on `.json()` / `.get()` fallback.**
3. `['email']` vs `.get('email','N/A')`? **`KeyError` vs `"N/A"`.**
4. Why `return` not `print` in a batch? **`return` gives it to the loop; print only shows.**
5. 429 + one line? **Too many requests; `time.sleep(1)`.**
6. What does the loop do with `"ok"`? **True→results, False→failures.**
7. `"w"` on re-run? **Erases the file first.**
8. Why can't the two files share fieldnames? **Different keys per row.**
9. `Sydney, UNKNOWN` without crashing — technique/why? **`.get()` fallbacks; Apollo records often incomplete.**
10. Line marking the Apollo swap + what changes? **The local lookup line; add `requests.get`, auth, status/JSON handling, rate limiting.**

### Pandas + ICP + n8n wrap-up — 9.5/10
1. Page 1 only — why dangerous? **You miss the rest of the data.**
2. What stops a `while True` pagination loop? **`if not has_more: break`; remove it → infinite.**
3. `pd.DataFrame(list_of_dicts)` turns dict/key into? **Row / column.**
4. Inner vs outer of `df[df["employees"]>5000]`? **Inner = mask; outer keeps Trues.**
5. Two-condition filter symbol + wrapping? **`&`, each in parentheses.**
6. Read `df.groupby("industry")["employees"].mean()`. **Average employees per industry.**
7. Why highest-threshold-first in banding? **Or a big value matches a lower band → wrong label.**
8. Why `size_points` reuses `size_band`? **No duplicated thresholds; one place to maintain (DRY).**
9. Why does the `reason` string matter? **Shows the calc → explainable/verifiable (defend every weight).**
10. `0 sent/4 failed` → `4 sent/0 failed`, what changed? **PUBLISHED the workflow — the production URL
    404s until the workflow is active, however correct the URL.** *(The fix was activation, not the URL.)*

---

## Interview framing (bank this)

> *"I built a batch enrichment pipeline and a weighted ICP scoring engine in Python. The pipeline takes
> a list of company domains, calls an API for each with graceful handling of failures, missing fields,
> pagination, and rate limits, and outputs clean enriched + review files. The scorer rates each company
> on industry fit, market, and size band — every weight chosen from the ICP, each score carrying a
> reason string — then POSTs the scored accounts into an n8n workflow via webhook. I can defend every
> weight."*

**Core habits:** never silently drop a failure (route it, with a reason); one source of truth (reuse
`size_band`); defend every weight; verify state before assuming (the API-deprecation and
"Published-vs-Active" webhook debugging).

---

## Week 3 — fully complete ✅
APIs & failure handling · batching + pacing · pagination · CSV persistence · pandas
(inspect/filter/group/band) · weighted ICP scorer (score/tier/reason) · batch POST into n8n
(4 landed in production). **Next: Week 4 (fresh thread)** — likely deeper pandas (merging enrichment
back onto lead lists) and beyond. Consider setting up a **virtual environment** first to fix the
multiple-Python-versions issue cleanly.
