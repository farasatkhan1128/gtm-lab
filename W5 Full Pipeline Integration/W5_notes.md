# Week 5 — Full Pipeline Integration

**Goal:** Stitch the separate scripts from Weeks 1–4 into one continuous, human-gated pipeline, and add the one new piece: a human approval gate.

**The one-line summary of the whole week:**
> A lead hits a webhook → a Flask microservice scores it + enriches it with a local LLM → the AI suggestion is posted to Slack for human approval → on approval, it's saved to CSV. The same engine also runs 50-lead batches unattended.

---

## 1. The data contract (Monday)

Every stage is a box that takes data in one shape and hands it out in another. The "contract" is which keys/types travel on each arrow. Wiring only works if each stage's output matches what the next expects. **The map IS the architecture answer in an interview.**

The record grows left to right:

```
{company, domain, industry, employees, country}   ← the real input (not just company+domain!)
        → + icp_score, tier                        (scoring adds these)
        → + outreach_line, pain_point, summary      (AI adds these)
        → + stage: "enriched"
        → + approved: true                          (approval adds this)
        → written to CSV
```

**Key correction from the week:** the input can't be just `{company, domain}`. `score_company` needs `industry`, `country`, `employees`, and `get_validated` needs `industry` separately. The lead arriving at the pipeline must already carry firmographics.

---

## 2. The architecture

**n8n is the orchestrator. Python logic is exposed as a microservice (Flask) that n8n calls over HTTP.**

Why: n8n runs inside Docker (Linux, no D: drive, no access to your venv), so it *can't* run your Python scripts directly. The clean, interview-worthy pattern is to wrap the logic as an HTTP endpoint and orchestrate it from n8n.

```
n8n Webhook  →  HTTP Request → Flask /process  →  Slack approval  →  HTTP Request → Flask /commit
   (receive)      (score + AI enrich)              (human gate)         (save to CSV)
```

- **Ollama stays put.** Only Python talks to it (localhost:11434). n8n never touches Ollama.
- `/process` and Ollama both live on the Windows host. n8n is in Docker.

### `service.py` — the two endpoints

- **`/process`** — takes a raw lead, runs `score_company` (scoring) then `get_validated` (Ollama AI enrichment), returns a flat enriched record. **Writes nothing** (so approval can sit before output).
- **`/commit`** — takes an enriched record, appends it to `pipeline_output.csv`. **Owns the CSV.**

Splitting "think" (`/process`) from "save" (`/commit`) is what makes the human approval gate possible — a human can sit between them and veto before anything is written.

---

## 3. Key concepts & gotchas (the stuff that actually bit)

### `host.docker.internal` — Docker → host networking
From *inside* a Docker container, `localhost` means the container itself, NOT your Windows machine. Docker Desktop provides the magic hostname `host.docker.internal` which resolves to the Windows host. So n8n's HTTP node must call:
```
http://host.docker.internal:5000/process   ✅
http://localhost:5000/process               ❌ (points at the container)
```
Fallback if it won't resolve: use the host's LAN IP directly (e.g. `http://192.168.1.181:5000/process`).

### `{{ $json }}` vs `{{ $json.body }}` — expression depends on the PREVIOUS node
Each n8n node sees the previous node's output as `$json`.
- The **Webhook** node wraps the incoming POST payload under a `body` key → the node after it uses `{{ $json.body }}` to unwrap the real lead.
- After **Process (Flask)**, its output is already the flat enriched record → the node after it uses `{{ $json }}`.

**The bug we hit:** after inserting the Slack gate before Commit, the node *before* Commit became Slack — whose output is just `{approved: true}`, not the lead. So `{{ $json }}` in Commit saved `{'approved': True}` instead of the record. Fix: reference the Process node by name to reach past Slack:
```
{{ $('Process (Flask)').item.json }}
```
**Lesson:** the correct expression always depends on what the immediately preceding node outputs.

### Body Content Type must be JSON (not stringified)
In the HTTP node, set **Body Content Type → JSON** and **Specify Body → Using JSON**. If it's sent as a stringified blob, Flask receives the wrong shape and `score_company` throws `KeyError: 'industry'`. This JSON setting is what made `{{ $json.body }}` pass through as a real object.

### Returned dicts must be flattened before CSV
`score_company` and `get_validated` return **whole dicts**, not single values. Stuffing a dict into `lead["icp_score"]` produces a dict-inside-a-dict, which a CSV cell can't hold cleanly. Lift the useful fields to the top level:
```python
score = score_company(lead)
lead["icp_score"] = score.get("icp_score")
lead["tier"] = score.get("tier")
ai = get_validated(lead.get("company"), lead.get("industry"))
lead["outreach_line"] = ai.get("outreach_line")
lead["pain_point"]    = ai.get("pain_point")
lead["summary"]       = ai.get("summary")
```

### File paths — don't hardcode the folder
Instead of `r"D:\gtm-lab\W5\..."` (which broke because the real folder is `W5 Full Pipeline Integration`), use:
```python
path = os.path.join(os.path.dirname(__file__), "pipeline_output.csv")
```
`__file__` = path to this script; `os.path.dirname` = its folder; `os.path.join` sticks the filename on. Always lands next to the script, survives folder renames. **Proper practice.**

### The `if __name__ == "__main__":` guard
Importing a Python module **runs the whole file top to bottom**, including loose code at the bottom. That's why `icp_score.py`'s demo block (the `Stripe | score 100` / `Sending... ERROR` spam) fired every time Flask started — `service.py` imports it.

`__name__` is a built-in: it equals `"__main__"` when the file is **run directly** (`python icp_score.py`), and the module name (`"icp_score"`) when **imported**. So:
```python
if __name__ == "__main__":
    # demo/test code here — only runs when you run THIS file directly,
    # NOT when another file imports it
```
Wrap all loose executable code in this guard. Functions and imports stay at top level (so they're importable); demo code goes under the guard.

### Ollama: CPU mode + RAM
- The GPU throws PTX/CUDA errors and lacks VRAM → run **CPU-only** via user env var `OLLAMA_LLM_LIBRARY=cpu`.
- The desktop app may launch a server process that doesn't inherit the env var → it tries GPU, OOMs, the model fails to load, and **every lead silently falls back to `[NEEDS REVIEW]`**.
- Even on CPU, the model needs ~1.3GB contiguous RAM. With Docker/n8n + Chrome + Slack all open, RAM fills up and loading fails with `failed to allocate CPU_REPACK buffer`. **Free up RAM** (close tabs/apps) and it loads.
- **Pre-flight ritual:** run `ollama run llama3.2:3b "hi"` — if it replies, the model loads and the pipeline will get real AI. If it OOMs, fix it BEFORE running a batch, or you get 50 × `[NEEDS REVIEW]`.

### Test webhooks fire ONCE
n8n's test URL (`/webhook-test/lead-intake`) only works for **one call**, and only **after** you click "Listen for test event". Arm it, then fire immediately. A 404 "webhook not registered" means it wasn't armed or was already consumed. (The live/published URL is `/webhook/lead-intake`.)

### The `[NEEDS REVIEW]` fallback is a FEATURE
When Ollama fails, `validated.py`'s retry-then-fallback layer (built in Week 4) catches it and stamps `[NEEDS REVIEW]` instead of crashing. This is **graceful degradation** — one dead dependency doesn't take down the whole run. In a real workflow, a `[NEEDS REVIEW]` lead is exactly what a human reviewer should *reject* rather than approve.

---

## 4. The human-in-the-loop approval gate (Friday)

**Why gate BETWEEN Process and Commit (not after Commit):**
An AI that writes outreach and saves it with zero review is a liability — it'll occasionally hallucinate. The gate catches bad output **before it's persisted**. If approval came *after* Commit, the row would already be saved and the veto would be meaningless. Gating before the write is what makes "reject = nothing saved" possible.

**How it works (n8n "Send and Wait for Response", Response Type = Approval):**
1. Node posts the enriched lead to Slack with an Approve button.
2. Workflow **pauses** at a waiting webhook.
3. Human clicks Approve → Slack hits `localhost:5678/webhook-waiting/...?approved=true` → workflow resumes → Commit runs.
4. No approval = nothing saved.

**Slack setup (free plan, no paid tier needed):**
- Create a Slack app at api.slack.com/apps → add bot scope `chat:write` → Install to Workspace → copy the `xoxb-` Bot User OAuth Token.
- In n8n: Slack credential → **Access Token** type → paste `xoxb-` token.
- Sending to a **Channel** (not User "From list") avoids needing the `users:read` scope.
- ⚠️ Never paste the `xoxb-` token in chat/screenshots; rotate it (Reinstall) if exposed.

---

## 5. Single leads vs. batches — a design decision

**Single/interactive leads → gated flow** (Webhook → Process → Slack → Commit). A human is in the loop anyway.

**Batches → run unattended, bypass the gate** (Process → Commit direct). A per-lead gate doesn't scale — 50 leads would mean clicking Approve 50 times. Real systems gate interactive leads and run trusted bulk jobs automatically. **Recognising WHEN to apply a control is the systems-design judgement, not just how to build it.**

The 50-lead batch (`batch_runner.py`) tests the *engine* (score + AI + save) at volume without n8n/Slack. Three batch-processing principles baked in:
1. **Error isolation** — one failed lead is logged and skipped; the run continues (`try/except ... continue`).
2. **Summary at the end** — processed / committed / failed / needs_review counts. Know the batch's health.
3. **Pacing** — `time.sleep(0.5)` between leads so CPU-bound Ollama isn't overwhelmed.

Result: 50/50 processed, 50/50 committed, 0 failed, 0 needs_review.

---

## 6. Commands cheat-sheet

**Start Flask (in venv, from W5 folder):**
```powershell
cd "D:\gtm-lab\W5 Full Pipeline Integration"
..\.venv\Scripts\Activate.ps1        # look for (.venv) prefix
python service.py                    # wait for "Running on http://0.0.0.0:5000"
```

**Test /process directly:**
```powershell
Invoke-RestMethod -Uri http://localhost:5000/process -Method Post -ContentType "application/json" -Body '{"company":"Acme Ltd","domain":"acme.com","industry":"Software","employees":120,"country":"United Kingdom"}'
```

**Test /commit directly:**
```powershell
Invoke-RestMethod -Uri http://localhost:5000/commit -Method Post -ContentType "application/json" -Body '{"company":"Acme Ltd",...,"icp_score":70,"tier":"B","stage":"enriched"}'
```

**Fire a lead at n8n (test webhook — arm it first!):**
```powershell
Invoke-RestMethod -Uri http://localhost:5678/webhook-test/lead-intake -Method Post -ContentType "application/json" -Body '{"company":"Delta Systems","domain":"deltasystems.io","industry":"SaaS","employees":150,"country":"United States"}'
```

**Ollama pre-flight (must reply before any batch):**
```powershell
ollama run llama3.2:3b "hi"
Invoke-RestMethod -Uri http://localhost:11434/api/tags   # lists loaded models
```

**Run the 50-lead batch:**
```powershell
python batch_runner.py
```

**Commit the week:**
```powershell
cd "D:\gtm-lab"
git add .
git commit -m "Week 5: full pipeline integration ..."
git push
```

---

## 7. Pre-flight checklist (before running the pipeline / a batch)

1. ☐ `ollama run llama3.2:3b "hi"` **replies** (model loads — free RAM if it OOMs)
2. ☐ Ollama is in **CPU mode** (`OLLAMA_LLM_LIBRARY=cpu`)
3. ☐ Flask running in the **venv** (`(.venv)` prefix, `Press CTRL+C to quit` showing)
4. ☐ Docker Desktop + n8n up (for the n8n path)
5. ☐ For test webhook: **arm it** (Listen for test event) immediately before firing

> A dead Ollama silently stamps `[NEEDS REVIEW]` on every lead. This check is the difference between a clean batch and 50 useless rows.

---

## 8. Interview talking points

- *"I wrapped my scoring and enrichment logic as a Flask microservice and orchestrated it from n8n with a Slack approval gate."*
- *"Single interactive leads go through human approval; trusted batch jobs run unattended — you gate the control where it adds value."*
- *"The AI enrichment has a retry-then-fallback layer, so a dead LLM degrades gracefully to `[NEEDS REVIEW]` instead of crashing the pipeline."*
- Real bugs I debugged (good stories): Docker→host networking (`host.docker.internal`), nested-dict flattening for CSV, the `$json` reference bug after inserting the gate, Ollama GPU/CPU/RAM, and the `__main__` import guard.

---

## Status: Week 5 COMPLETE ✅
Mon (contract) · Tue (Flask + n8n) · Wed (Ollama in /process) · Thu (CSV via /commit) · Fri (Slack gate) · Sun (50-lead batch + cleanup + commit) · Ship (single + batch clean) · Quiz (100%)
