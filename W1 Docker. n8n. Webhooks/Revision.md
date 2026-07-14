# Week 1 Complete Revision — All Concepts & Quiz Answers

Study this before Week 2 starts, or before any interview.

---

## Docker & Self-Hosting

**Image vs Container:** Image = blueprint/recipe, static and reusable. Container = running instance made from that image.

**Volume:** Persistent storage on your machine, independent of any container. Container is disposable; volume survives reboots.

**Docker Desktop vs docker command:** Docker Desktop = the engine (the app). docker command = remote control. Engine off = commands fail.

**Why `docker ps` errored:** Docker Desktop wasn't running. The command is just a remote control.

---

## Webhooks & n8n

**Webhook:** A URL that waits for incoming data. When another system POSTs JSON to it, the workflow fires automatically. Push, not pull.

**In Clay → CRM:** Clay POSTs enriched data to your webhook → n8n workflow catches it, validates, scores, routes it → pushes into CRM.

**The `body` wrapper:** n8n wraps webhook data inside a `body` object. Path to company name is `body.company_name`, not just `company_name`. The dot means "go inside."

---

## JSON

**4 building blocks:** String (text in quotes), Number (no quotes), Array (list in [ ]), Object (mini-form in { }).

**Zero-based indexing:** `tags[0]` is the FIRST item, `tags[1]` is second. Everyone stumbles once.

**Nesting:** Use a dot to go inside. `location.country` = go into location, grab country.

**String vs Number:** `"45"` is text, `45` is a number. Different types, different behaviour.

---

## Python

**Dictionary vs JSON:** Same structure in two places. JSON travels over the web. Dictionary is how Python holds it. Identical shape.

**Reading a field:** In n8n: `$json.body.company_name`. In Python: `lead["company_name"]`. Same idea, different syntax.

**Keys are case-sensitive:** `"Company_name"` and `"company_name"` are different keys. Mismatch = KeyError.

**Functions:** `def name(input):` makes a reusable machine. `return` gives back the result.

**Indentation defines scope:** Left margin = outside function. 4 spaces = inside function. 8 spaces = inside an if inside the function.

**Accumulating a score:** Start at 0, add points as rules pass. Collect reasons as you go.

**elif:** "else if" — checked only if the previous condition failed.

---

## The ICP Scoring Engine

**What it does:** Takes a lead (dictionary), runs 3 weighted rules, returns `{ icp_score, tier, reason }`.

**Rules:** UK market (+25), Beauty industry (+30), Employees >= 20 (+30).

**Tiering:** >= 80 = Tier 1, >= 50 = Tier 2, < 50 = Tier 3.

**Why the reason matters:** A salesperson can't act on "85". But "UK beauty company, right size" tells them how to pitch. The reason is what makes the score actionable.

**Proof it discriminates:** Strong lead → 85/Tier 1 with reason. Weak lead → 0/Tier 3 empty reason. A good engine separates.

---

## Git & GitHub

**push vs pull:** `git push` = send local commits UP to GitHub (laptop → cloud). `git pull` = download GitHub commits DOWN (cloud → laptop).

**Why pull matters:** When you edit in two places, they drift. Pull brings remote changes down to sync.

**Untracked file error:** Git refuses to overwrite a local file that's not in its history. Decide which version to keep, remove the other, then pull. Git is protecting you.

---

## Interview One-Liners

- "I use n8n for orchestration and Python for the data logic."
- "Container = disposable, volume = persistent. Workflows survive reboots because they live in a named volume."
- "Webhook is the entry point for enriched data from Clay, validated, scored, routed into CRM."
- "Every enrichment tool speaks JSON. Field mapping between them is most of the real work."
- "Reason matters as much as score. Salesperson can't act on '85', but can act on 'UK beauty company, right size'."
