# Self-Hosted AI GTM Research Assistant

A self-hosted automation lab that takes raw company/lead data, cleans and
validates it, scores it against an Ideal Customer Profile (ICP), and generates
a summary, likely pain point and personalised outreach line — with a
human-in-the-loop approval step before anything is actioned.

Built to demonstrate GTM Engineering skills: self-hosting, webhooks, JSON,
Python data pipelines, rule-based lead scoring, and (later) local AI.

---

## Why this exists

Most GTM teams argue about "what is a good lead" and route them by gut feel.
This project encodes that judgement into transparent, weighted rules, wires it
into an automation pipeline, and keeps a human in control of any sensitive
action. It mirrors the real work of moving enriched account data from tools
like Clay or Apollo into a CRM with cleaning, validation, scoring and routing.

---

## Architecture (target)

```
Lead / company data
        |
        v
   n8n webhook              (self-hosted intake)
        |
        v
   Python pipeline          (clean, dedupe, validate, ICP score)
        |
        v
   Local AI (Ollama)        (summary, pain point, outreach line)
        |
        v
   n8n workflow             (store to Sheet / CSV / CRM-style output)
        |
        v
   Human approval           (AI suggests -> human approves -> execute)
```

Safe-design principle: the AI never directly sends email, writes to the CRM,
or runs sensitive actions. It generates suggestions; n8n validates; a human
approves; only then does the workflow execute.

---

## Tech stack

- **Docker** — self-hosting n8n in a container with a persistent volume
- **n8n** — workflow orchestration and webhook intake
- **Python 3** — data cleaning, deduplication, validation and ICP scoring
- **Ollama** (planned) — local AI for summaries and outreach copy
- **Git / GitHub** — version control and documentation

---

## Progress

### Week 1 — Docker, n8n, webhooks, JSON, Python foundations  ✅
- Self-hosted n8n in Docker with a named volume (workflows persist across
  restarts).
- Built a Lead Intake workflow: Webhook (POST) → Edit Fields → Respond to
  Webhook. Receives a lead as JSON and maps nested fields.
- Learned JSON structure (objects, arrays, nesting, the `body` wrapper) and
  field mapping via dot-paths.
- Wrote a Python ICP scoring engine that takes a lead and returns
  `{ icp_score, tier, reason }` using transparent weighted rules.
  Tested on a strong lead (85 / Tier 1) and a weak lead (0 / Tier 3).

### Week 2 — Python for GTM data: a full cleaning + scoring pipeline  ✅
Built `clean_leads.py` — a complete batch pipeline that turns a messy raw
export into a prioritised, tiered lead list.

**What it does:**
1. **Reads** a raw CSV export as a list of dictionaries (`csv.DictReader`)
2. **Deduplicates** on **domain**, not company name — domains are unique
   identifiers; names get typo'd and given suffixes ("Zen Clinic Ltd" vs
   "ZEN CLINIC" vs "Zen Clinic")
3. **Normalises** company names — trims whitespace, strips legal suffixes
   (Ltd / Limited), standardises casing
4. **Validates** required fields — records missing an employee count are routed
   to a separate review file rather than silently dropped
5. **Converts types** — CSVs return everything as strings, so employee counts
   are cast to integers before any numeric comparison
6. **Scores** every surviving lead with the Week 1 ICP engine
7. **Sorts** by score, highest first, and writes `leads_scored.csv`

**Design decisions worth noting:**
- Dedup runs on domain because it's a reliable unique key
- Cleaning runs *before* dedup — you can only match duplicates once both
  records are normalised to the same form
- Dropped records are **logged**, not silently removed. Every input is
  accounted for as clean, duplicate, or review — 8 + 1 + 1 = 10
- Incomplete records are **routed to review**, not deleted, so a human can fix
  them

### Coming next
- Week 3: APIs, requests, pandas, expanded ICP scoring
- Week 4: Local AI (Ollama) for summaries and outreach lines
- Week 5: Full pipeline integration (n8n ↔ Python ↔ AI) with human approval
- Week 6: Hardening — Docker Compose, webhook auth, logging, VPS deployment
- Week 7: Portfolio packaging (diagram, demo, docs)
- Week 8: Interview readiness

---

## Example

**Input** (raw export, `leads.csv` — messy, with a duplicate and a missing field):
```csv
company_name,domain,industry,country,employees
Glow Beauty London,glowbeauty.co.uk,Beauty,United Kingdom,45
fresh hair studio,freshhairstudio.co.uk,Hair Salon,United Kingdom,8
Zen Clinic Ltd,zenclinic.co.uk,Med Spa,United Kingdom,12
Pure Spa Limited,purespa.co.uk,Spa,United Kingdom,
Glow Beauty London,glowbeauty.co.uk,Beauty,United Kingdom,45
...
```

**Output** (`leads_scored.csv` — cleaned, deduped, validated, scored, ranked):
```
Tier 1 | 85 | Glow Beauty London  | UK market, target industry (beauty), suitable team size
Tier 2 | 55 | Bright Smile Dental | UK market, suitable team size
Tier 3 | 30 | Alpine Wellness     | suitable team size
Tier 3 | 25 | Fresh Hair Studio   | UK market
Tier 3 | 25 | Zen Clinic          | UK market
Tier 3 |  0 | Nordic Skin Co      |
```

Plus `leads_review.csv` containing the one record with a missing employee count.

The **reason** field matters as much as the score: a salesperson can't act on
"85", but "UK beauty company, right size" tells them how to pitch.

---

## Repo structure

```
gtm-lab/
├── README.md
├── W1 Docker. n8n. Webhooks/     Docker, n8n webhook workflow, ICP scoring engine
├── W2 Python for GTM Data/       CSV cleaning, dedup, validation, batch scoring
└── ...                            (W3–W8 to follow)
```

Each week folder contains the working code plus daily lab notes documenting the
concepts, design decisions, and bugs encountered.

---

*Built as an 8-week GTM Engineering lab. Work in progress.*
