# Self-Hosted AI GTM Lab — Notes

## Day 4 — Python Starts: Reading the Same JSON Shape (8 Jul 2026)

### Core idea of the day
A Python DICTIONARY is basically a JSON OBJECT. Same curly braces, same
key-value pairs. This is the bridge between n8n and Python: I keep the data
shape identical on both sides so the handoff is clean.

  JSON (in n8n):   { "company_name": "Glow Beauty London", "employees": 45 }
  Python dict:     { "company_name": "Glow Beauty London", "employees": 45 }

### Why n8n AND Python (interview point)
n8n is great for orchestration (wiring tools together). But when the logic
gets real — deduping thousands of rows, weighted scoring, cleaning messy
company names — Python is the right tool. Strong interview line:
"I use n8n for orchestration and Python for the data logic."

### Reading a field
In n8n I used a dot:      $json.body.company_name
In Python I use brackets: lead["company_name"]
Same idea: "go get this key". Different syntax.

### Keys are CASE-SENSITIVE (learned today)
"Company_name" and "company_name" are TWO DIFFERENT keys in Python.
If my code asks for a key that doesn't exist, I get a KeyError.
I first wrote the key with a capital C, then fixed it to lowercase
company_name so it matches the real webhook data. Mismatched casing
between an enrichment tool and my script is a classic real-world bug.

### The building blocks I used
- Variable = a labelled box holding a value:   score = 45
- String = text in quotes:   "Beauty"
- Number = no quotes:   45   (can do maths / comparisons)
- print() = shows a value on screen (my window into the code)
- if / else = make a decision based on a condition

### The script I wrote (score_lead.py)
```python
# A lead, same shape as the n8n webhook data
lead = {
    "company_name": "Glow Beauty London",
    "domain": "glowbeauty.co.uk",
    "industry": "Beauty",
    "country": "United Kingdom",
    "employees": 45
}

# Read individual fields (same idea as body.company_name in n8n)
print("Company:", lead["company_name"])
print("Country:", lead["country"])
print("Employees:", lead["employees"])

# First bit of logic — an if that checks a number (seed of ICP scoring)
if lead["employees"] >= 20:
    print("Team size: big enough to care about")
else:
    print("Team size: probably too small")
```

### Output it produced
```
Company: Glow Beauty London
Country: United Kingdom
Employees: 45
Team size: big enough to care about
```
(45 >= 20 is True, so the first branch printed.)

### How to run it
In VS Code terminal, from the gtm-lab folder:
  python score_lead.py
Note: my project lives on E:\CLAUDE\gtm-lab — that's where the repo will be.

### Common errors + fixes
- "python not recognised" -> PATH issue; try `py --version` or reinstall
  ticking "Add Python to PATH".
- KeyError: 'x' -> misspelled or wrong-case key; keys must match exactly.
- IndentationError -> lines under an if/else must be indented 4 spaces.
- Nothing prints -> file wasn't saved (Ctrl+S) before running.

### Interview explanation (say out loud)
"I keep n8n for orchestration and drop into Python when the logic gets real.
My scoring script loads a lead as a dictionary — the same structure as the
webhook JSON — reads the fields, and applies rules. Keeping the data shape
identical across n8n and Python means the handoff between them is clean."

### Why this matters for GTM Engineering
The if-statement checking employees >= 20 is the seed of ICP scoring. Next
step is turning simple checks into a weighted scoring function that outputs
a score, tier and reason — the engine of the GTM Research Assistant.
