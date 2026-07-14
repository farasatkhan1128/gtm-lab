# Self-Hosted AI GTM Research Assistant

A self-hosted automation lab that takes raw company/lead data, validates and
scores it against an Ideal Customer Profile (ICP), and generates a summary,
likely pain point and personalised outreach line — with a human-in-the-loop
approval step before anything is actioned.

Built to demonstrate GTM Engineering skills: self-hosting, webhooks, JSON,
Python data logic, rule-based lead scoring, and (later) local AI.

---

## Why this exists

Most GTM teams argue about "what is a good lead" and route them by gut feel.
This project encodes that judgement into transparent, weighted rules, wires it
into an automation pipeline, and keeps a human in control of any sensitive
action. It mirrors the real work of moving enriched account data from tools
like Clay or Apollo into a CRM with validation, scoring and routing.

---

## Architecture (target)

```
Lead / company data
        |
        v
   n8n webhook              (self-hosted intake)
        |
        v
   Python script            (clean, validate, ICP score)
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
- **Python 3** — data cleaning, validation and ICP scoring logic
- **Ollama** (planned) — local AI for summaries and outreach copy
- **Git / GitHub** — version control and documentation

---

## Progress

### Week 1 — Docker, n8n, webhooks, JSON, Python foundations  ✅
- Self-hosted n8n in Docker with a named volume (workflows persist across
  restarts).
- Built a Lead Intake workflow: Webhook (POST) -> Edit Fields -> Respond to
  Webhook. Receives a lead as JSON and maps nested fields.
- Learned JSON structure (objects, arrays, nesting, `body` wrapper) and field
  mapping via dot-paths.
- Wrote a Python ICP scoring engine (`score_lead.py`) that takes a lead and
  returns `{ icp_score, tier, reason }` using transparent weighted rules.
  Tested on a strong lead (85 / Tier 1) and a weak lead (0 / Tier 3).

### Coming next
- Week 2: CSV cleaning, deduplication, missing-field handling at scale
- Week 3: APIs, requests, pandas, expanded ICP scoring
- Week 4: Local AI (Ollama) for summaries and outreach lines
- Week 5: Full pipeline integration (n8n <-> Python <-> AI) with human approval
- Week 6: Hardening — Docker Compose, webhook auth, logging, VPS deployment
- Week 7: Portfolio packaging (diagram, demo, docs)
- Week 8: Interview readiness

---

## Files

| File | What it is |
|------|------------|
| `score_lead.py` | The ICP scoring engine — takes a lead, returns score/tier/reason |
| `lab-notes.md` | Day 1 learning notes (Docker, n8n, webhooks) |
| `lab-notes-day2.md` | Docker concepts, container vs volume |
| `lab-notes-day3.md` | JSON in depth, field mapping |
| `lab-notes-day4.md` | Python basics, dicts vs JSON |
| `lab-notes-day5.md` | The ICP scoring engine |
| `quiz-revision.md` | Running self-test bank of concepts |

---

## Example

Input:
```json
{
  "company_name": "Glow Beauty London",
  "domain": "glowbeauty.co.uk",
  "industry": "Beauty",
  "country": "United Kingdom",
  "employees": 45
}
```

Output:
```json
{
  "icp_score": 85,
  "tier": "Tier 1",
  "reason": "UK market, target industry (beauty), suitable team size"
}
```

---

*Built as an 8-week GTM Engineering lab. Work in progress.*
