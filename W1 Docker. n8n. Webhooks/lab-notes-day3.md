# Self-Hosted AI GTM Lab — Notes

## Day 3 — JSON in Depth + Reading Fields from a Lead (8 Jul 2026)

### Core idea of the day
JSON is just labelled boxes. Some boxes hold a plain answer, some hold a
list, some hold more boxes. You reach inside boxes with a dot.
Being able to read and map nested JSON is most of real GTM Engineering —
every enrichment tool and CRM (Clay, HubSpot, Apollo, Lusha) speaks it.

### The four JSON building blocks
- **String** = text, always in quotes.  "Glow Beauty London"
- **Number** = a plain number, no quotes.  45  (can do maths / scoring on it)
- **Array** = a list in square brackets.  ["beauty", "ecommerce", "uk"]
- **Object** = a mini-form in curly braces.  { "city": "London" }

Gotcha: "45" (string) is NOT the same as 45 (number).
Quotes = text, no quotes = number. Mixing them up is a classic bug —
e.g. an enrichment tool sends employees as "45" but scoring expects 45.

### Nesting = a box inside a box
A value can be another whole object. To reach a field inside it, write a
PATH using dots. The dot means "go inside".
  location.country  ->  go into location, then grab country  ->  "United Kingdom"

### Arrays start counting at ZERO
  tags = ["beauty", "ecommerce", "uk"]
  tags[0] = "beauty"   (first item)
  tags[1] = "ecommerce"
  tags[2] = "uk"
First item is position 0, not 1. Everyone trips on this once.

### The n8n `body` wrapper (important)
When a lead arrives via the webhook, n8n wraps it inside a `body` object.
So the real path to the company name is:
  $json.body.company_name    (NOT just $json.company_name)
Top-level boxes I saw in the webhook output: headers, params, query, body,
webhookUrl, executionMode. My actual lead data lives inside `body`.
- $json = "the data coming into this node"
- .body.company_name = the journey to the field I want
Forgetting `.body.` gives "undefined" — the most common beginner error.

### What I built today
Upgraded Lead Intake: Webhook -> Edit Fields (Set) -> Respond to Webhook.
The Edit Fields node reaches into the nested lead and pulls out 3 clean
fields using expressions:
  company  =  {{ $json.body.company_name }}   -> Glow Beauty London
  size     =  {{ $json.body.employees }}      -> 45
  market   =  {{ $json.body.country }}        -> United Kingdom

### Debugging note (learned the hard way)
1. First curl attempt landed with EMPTY body fields = request arrived but
   the JSON didn't parse (Windows PowerShell curl quoting). Fix: use
   Invoke-RestMethod with ConvertTo-Json, or the exact escaped curl.exe.
   Lesson: "request came in but fields are blank" = a body/format problem,
   not a connection problem. Same thing happens with real enrichment tools.
2. An accidental blank field showed up as an `empty` column in the output.
   Fix: delete the half-created field, re-run. Always check the output has
   exactly the columns you expect and nothing extra.

### Reading data in n8n
The node output can be viewed as Table / JSON / Schema.
- JSON view = raw structure (shows the body wrapper)
- Schema view = the field tree (the "map")
The INPUT panel on the left shows the full incoming tree; my fields live
under the `body` branch.

### Interview explanation (say out loud)
"My intake workflow receives a lead as nested JSON, then maps the fields I
need — company name, size, market — using field paths, before passing them
downstream for scoring. Navigating nested JSON is essential in GTM
Engineering because every enrichment tool and CRM speaks it, and field
mapping between them is most of the real work."

### Why this matters for GTM Engineering
When a Clay enrichment returns a company, it's JSON. When I push a contact
to HubSpot's API, it's JSON. If I can't read a nested field path I can't
debug why "the domain isn't mapping" or "the enrichment came back empty".
Today's dot-path skill is the exact same logic Python will use next week.
