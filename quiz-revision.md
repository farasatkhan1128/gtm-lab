# Self-Hosted AI GTM Lab — Quiz Revision

A running record of every quiz question and its answer.
Use this to refresh before interviews. Try to answer from memory FIRST,
then check. The ones you get wrong are the ones that stick.

---

## DAY 1 — Docker, n8n, Webhooks

**Q1. What's the difference between a Docker image and a container?**
An image is the blueprint/recipe — static and reusable (e.g. n8nio/n8n).
A container is a running instance made from that image. One image can
produce many containers. Recipe = image, cooked dish = container.

**Q2. `docker ps` gave an error but nothing was broken. Why?**
The `docker` command talks to the Docker engine (Docker Desktop). If the
engine isn't running, the command fails even though nothing is broken.
The command is a remote control; the engine is the thing doing the work.
Fix: open Docker Desktop, wait for "Engine running", try again.

**Q3. Why did my Lead Intake workflow survive a reboot? What saved it?**
The VOLUME (n8n_data) saved it. The container is disposable — it was
stopped and rebuilt. My work survived because it lives in the volume,
which is persistent storage Docker manages on my machine, independent of
any container. The container could NOT have saved it, because containers
are ephemeral. Container = disposable compute, volume = persistent data.

**Q4. What does `-p 5678:5678` do?**
It maps port 5678 on my machine to port 5678 inside the container. That's
why http://localhost:5678 reaches n8n — my laptop's door 5678 forwards to
the container's door 5678.

**Q5. What is a webhook, and where does it sit in a Clay -> CRM pipeline?**
A webhook is a URL that waits for incoming data and triggers a workflow
when data is POSTed to it (push, not pull). In a Clay -> CRM pipeline it
sits between Clay and n8n/CRM: it receives enriched lead data from Clay,
then the workflow validates, scores, routes and pushes it into HubSpot.

**Q6. The terminal showed 200 OK. What does that mean?**
The server received my request, processed it successfully, and sent back a
valid response. It proved the full round trip worked — n8n accepted the
Glow Beauty payload AND returned my JSON reply.

---

## DAY 2 — Docker Concepts, Hands-On

**Q1. Container vs volume in one line?**
Container = disposable compute. Volume = persistent data.

**Q2. Why was n8n already running when I reopened Docker Desktop?**
Docker Desktop remembers containers and auto-resumes them when the engine
starts. Opening Docker Desktop turned the engine back on, which restarted
my n8n container from the day before.

**Q3. What's the difference between the docker command and Docker Desktop?**
Docker Desktop (the whale app) is the ENGINE — it does the real work of
running containers. The `docker` command in PowerShell is a REMOTE CONTROL
that sends instructions to the engine. Engine off = commands fail.

**Q4. Where does a volume actually store data?**
In Docker's own managed storage on my machine (on Windows, inside the
WSL/Docker data area — not a normal folder I browse to). The point: it's
outside the container, on my machine, and it survives restarts.

---

## DAY 3 — JSON in Depth + Field Mapping

**Q1. In `$json.body.company_name`, what does `.body.` do?**
It steps into the `body` object, where n8n puts the real incoming lead
data. Without it, `$json.company_name` looks at the top level, doesn't
find the field, and returns undefined. (Most common beginner error.)

**Q2. `tags = ["beauty", "ecommerce", "uk"]` — what is tags[0]?**
"beauty" — the first item. Arrays count from ZERO, so tags[0] is the 1st,
tags[1] is "ecommerce", tags[2] is "uk".

**Q3. Is 45 the same as "45"?**
No. 45 is a number, "45" is a string. Different types, behave differently
(you can do maths on 45, not on "45"). Quotes = text, no quotes = number.

**The 4 JSON building blocks:**
- String = text in quotes         "Glow Beauty London"
- Number = no quotes              45
- Array  = list in [ ]            ["beauty", "ecommerce"]
- Object = mini-form in { }       { "city": "London" }

---

## DAY 4 — Python Starts

**Q4. Relationship between a Python dictionary and a JSON object?**
They're the same structure in two places. JSON is the format data travels
in over the web; a dictionary is how Python holds that same shape. Same
curly braces, same key-value pairs. When webhook JSON arrives in Python it
becomes a dict, read with the same "get this key" logic.
One-liner: "JSON is the format data travels in; a dictionary is how Python
holds that same shape."

**Q5. In `lead["country"]`, what do the square brackets do?**
They fetch the value stored under the key "country" from the lead
dictionary -> "United Kingdom". Same job as the dot-path in n8n, different
syntax (brackets instead of a dot).

**Q6. Why did "Team size: big enough to care about" print?**
Because employees is 45, and 45 >= 20 is True, so the `if` branch ran
instead of the `else` branch.

**Key gotcha from Day 4:**
Python keys are CASE-SENSITIVE. "Company_name" and "company_name" are two
different keys. Mismatched casing between an enrichment tool and my script
causes a KeyError.

---

## Running interview one-liners (collect the best here)
- "I use n8n for orchestration and Python for the data logic."
- "Container = disposable compute, volume = persistent data. My workflows
   persist across restarts because they live in a named volume."
- "A webhook is the entry point for enriched account data from Clay, which
   then gets validated, scored, routed and pushed into the CRM."
- "Every enrichment tool and CRM speaks JSON, and field mapping between
   them is most of the real work."
