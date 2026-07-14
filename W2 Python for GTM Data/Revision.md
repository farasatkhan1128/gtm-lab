# Week 2 — Python for GTM Data — Notes

Goal for the week: go from scoring ONE lead I typed by hand (Week 1) to
handling MANY real leads from a CSV file — loop, flag, clean, dedupe, score,
and write results back out. This is the tooling behind the "2,700+ records at
92% accuracy" story.

---

## MONDAY — Variables, lists, dictionaries (a list of dicts)

### Core idea
A single lead = a dictionary (Week 1). Many leads = a LIST of dictionaries.
```python
leads = [
    { "company_name": "Glow Beauty London", "industry": "Beauty", ... },
    { "company_name": "Fresh Hair Studio",  "industry": "Hair Salon", ... },
    { "company_name": "Zen Clinic",         "industry": "Med Spa", ... }
]
```
- The outer [ ] is a LIST (ordered collection).
- Each { } inside is a DICTIONARY (one lead record).
- So `leads` is a list of dictionaries.

### Key distinction (the concept the whole week rests on)
- **leads**  = the WHOLE collection (all the records in the list)
- **lead**   = ONE individual record, handed to me one at a time by the loop

### Looping over records
```python
for lead in leads:
    print(f"{lead['company_name']} is a {lead['industry']} business with {lead['employees']} employees.")
```
- `for lead in leads:` walks through each record in turn.
- On each pass, `lead` becomes the next dictionary in the list.
- `lead['company_name']` reads a field from that one record.

### f-strings
```python
f"{lead['company_name']} is a {lead['industry']} business"
```
- The `f` before the quotes = "formatted string".
- Anything inside `{ }` gets replaced with the real value.
- Lets me drop variables straight into text.

### What I built (Monday)
`lead_record.py` — a hardcoded list of 3 leads (Glow Beauty, Fresh Hair
Studio, Zen Clinic), looped over with a for loop, printing a sentence per
lead using an f-string. Output = 3 clean sentences. Confirmed working.

---

## TUESDAY — if statements + for loops (flagging), and reading a real CSV

### Reading leads FROM A FILE (the real-world version)
Nobody types 2,700 leads by hand — they come from an export. So instead of a
hardcoded list, read from a CSV:
```python
import csv

with open("Week 2/leads.csv", "r") as file:
    reader = csv.DictReader(file)
    leads = list(reader)
```
- `import csv` = bring in Python's built-in CSV toolkit.
- `with open(...) as file` = open the file safely (auto-closes when done).
- `csv.DictReader` = reads each ROW as a DICTIONARY, using the header row as
  the keys. So every row becomes { "company_name": ..., "industry": ... } —
  the exact same shape as the hardcoded version.
- `list(reader)` = turn all the rows into a list of dicts called `leads`.

Big point: the for loop that reads the data is IDENTICAL whether the data was
hardcoded or read from a file. The file just replaces the typing.

### Flagging with if INSIDE the loop
Tuesday's real skill: don't just print each lead — make a DECISION about it.
```python
for lead in leads:
    if lead["country"] == "United Kingdom" and lead["industry"] == "Beauty":
        print(f"UK BEAUTY LEAD: {lead['company_name']}")
    else:
        print(f"skip: {lead['company_name']}")
```
- The `if` runs a check on EACH lead as it passes through the loop.
- `and` = BOTH conditions must be true (UK AND Beauty).
- This is FILTERING — the foundation of lead routing and segmentation.

### What I built (Tuesday)
`read_leads.py` — reads 10 leads from `leads.csv`, loops over them, and flags
UK Beauty companies vs skips. Only Glow Beauty London matched.

### Bug/insight caught by my own code
Glow Beauty London got flagged TWICE — because it appears twice in the CSV
(a duplicate). My code surfaced exactly why DEDUPLICATION matters: without it,
sales would get the same lead twice. (Dedup is Thursday's job.)

### The messy data I'm now working with (leads.csv)
Deliberately realistic problems, visible in the output:
- Inconsistent case: "fresh hair studio" (lower), "BRIGHT SMILE DENTAL" (upper)
- Company suffixes: "Zen Clinic Ltd", "Pure Spa Limited", "Lux Aesthetics ltd"
- A duplicate: Glow Beauty London appears twice
- A missing field: Pure Spa has no employee count (prints a blank gap)
- Non-UK leads: Alpine Wellness (Germany), Nordic Skin Co (Sweden)
Each of these is a cleaning job for the days ahead.

---

## QUIZ QUESTIONS + ANSWERS (Mon–Tue)

**Q1. What is a list of dictionaries, and why use one for leads?**
A list (ordered collection) where each item is a dictionary (one lead record).
Perfect for leads because I have many records, each with the same fields.

**Q2. What's the difference between `leads` and a single `lead`?**
`leads` = the whole collection (all records). `lead` = one individual record,
handed to me one at a time by the loop.

**Q3. What does `csv.DictReader` do?**
Reads each row of a CSV as a dictionary, using the header row as the keys. So
each row comes out in the same shape as a hardcoded lead dict.

**Q4. What does an `if` inside a `for` loop let me do?**
Make a decision about EACH record as the loop passes over it — e.g. flag it or
skip it. This is filtering.

**Q5. What does `and` mean in a condition?**
Both conditions must be true for the `if` to run. `UK and Beauty` = only leads
that are both UK and Beauty match.

**Q6. Why did Glow Beauty get flagged twice?**
Because it appears twice in the CSV — a duplicate. Shows why dedup matters.

**Q7. (Case-sensitivity recap from Week 1)** Why did `For lead in leads:` error?**
Python is case-sensitive. The keyword is lowercase `for`; `For` is not
recognised. Same reason "Company_name" != "company_name".

---

## Terminology quick list
- list           ordered collection, in [ ]
- dictionary     key-value record, in { }
- list of dicts  many records = the shape of a lead list
- import         bring in a Python toolkit (e.g. import csv)
- csv.DictReader reads each CSV row as a dictionary
- for loop       walk through each item in a collection
- if / else      make a decision
- and            both conditions must be true
- f-string       f"...{value}..." drops variables into text
- duplicate      the same record appearing more than once
- (dedup)        removing duplicates — coming Thursday

---

## Interview one-liners (Week 2 so far)
- "I read lead exports from CSV into Python as a list of dictionaries, then
   loop over them to filter, clean and score."
- "An if inside the loop lets me flag or route each record — the basis of
   segmentation."
- "My own code surfaced a duplicate lead, which is exactly why deduplication
   is a required step before anything reaches the CRM."


---

## WEDNESDAY — Functions: clean_company_name()

### Core idea
Messy company names break everything downstream. "Zen Clinic Ltd", "ZEN CLINIC"
and "zen clinic" look like three different companies to a CRM, but they're one.
A cleaning (normalisation) function standardises them so dedup, matching and
reporting actually work. This is the tooling behind the "92% CRM accuracy" story.

### String methods (Python's built-in text tools)
Attach them to a string with a dot:
- `.strip()`              removes whitespace from start and end
                          "  Zen  ".strip()  ->  "Zen"
- `.replace(old, new)`    swaps text
                          "Zen Clinic Ltd".replace(" Ltd", "")  ->  "Zen Clinic"
- `.title()`              capitalises each word
                          "fresh hair studio".title()  ->  "Fresh Hair Studio"

These CHAIN — apply one after another, each step tidying a bit more.

### The cleaning function
```python
def clean_company_name(name):
    name = name.strip()                    # trim spaces
    name = name.replace(" Limited", "")    # strip "Limited"
    name = name.replace(" Ltd", "")        # strip "Ltd"
    name = name.replace(" ltd", "")        # strip lowercase "ltd"
    name = name.title()                    # fix capitalisation
    return name
```
Read it top to bottom: the name comes in, each line reassigns `name` to its
cleaned-up self, and `return` hands back the finished version.

### What `return` does (locked this in)
`return` HANDS BACK the result from the function to whoever called it.
Without it, the function does the work but keeps the answer to itself.
```python
cleaned = clean_company_name("fresh hair studio")
# the function cleans it, then return hands back "Fresh Hair Studio"
# which lands in the variable `cleaned`
```
One-liner: "return is what hands the result back to whoever called the function."

### ORDER MATTERS in a cleaning pipeline
`.title()` runs LAST on purpose. If suffixes were stripped after titling, the
replace (which looks for " Ltd") could miss variants. The sequence of cleaning
steps is a deliberate design decision, not an accident.

### Running it across the real CSV (not just test strings)
```python
import csv

with open("W2 Python for GTM Data/leads.csv", "r") as file:
    leads = list(csv.DictReader(file))

for lead in leads:
    cleaned = clean_company_name(lead["company_name"])
    print(f"{lead['company_name']}  ->  {cleaned}")
```

### Results (before -> after)
```
fresh hair studio      ->  Fresh Hair Studio
Zen Clinic Ltd         ->  Zen Clinic
BRIGHT SMILE DENTAL    ->  Bright Smile Dental
Pure Spa Limited       ->  Pure Spa
Lux Aesthetics ltd     ->  Lux Aesthetics
Glow Beauty London     ->  Glow Beauty London   (already clean, unchanged)
Alpine Wellness        ->  Alpine Wellness      (already clean, unchanged)
```
Note: "  Lux Aesthetics ltd  " had leading whitespace, trailing whitespace AND
a lowercase suffix — all three handled by the chained pipeline.

### KEY INSIGHT: clean BEFORE dedup
Both copies of "Glow Beauty London" now normalise to the IDENTICAL string.
That's exactly why cleaning comes first: you can only spot duplicates reliably
once both versions have been standardised to the same form. If one said
"Glow Beauty London Ltd" and the other "glow beauty london", a naive dedup
would miss them completely.

### Known limitation (good to mention in interviews)
`.title()` mangles names like "McDonald" -> "Mcdonald". Real-world normalisation
needs exception handling for these. Knowing the edge case matters more than
pretending the function is perfect.

---

## QUIZ QUESTIONS + ANSWERS (Wednesday)

**Q8. What do .strip(), .replace() and .title() each do?**
.strip() removes leading/trailing whitespace. .replace(old, new) swaps text.
.title() capitalises each word.

**Q9. What does `return` do in a function?**
It hands the result back to whoever called the function. Without it, the
function does work but you never get the answer out.

**Q10. Why does .title() run last in the cleaning pipeline?**
Order matters — stripping suffixes after titling could cause the replace to
miss variants. The sequence is a deliberate design choice.

**Q11. Why do we clean company names BEFORE deduplicating?**
Because dedup relies on exact matches. Two records for the same company only
look identical after normalisation. Clean first, then dedupe.

**Q12. Why is cleaning important for a CRM?**
"Zen Clinic Ltd", "ZEN CLINIC" and "zen clinic" are one company but look like
three. Without normalisation, dedup fails, matching fails, and reporting is
wrong.

---

## Terminology added (Wednesday)
- string method     a built-in text tool attached with a dot (.strip(), .title())
- normalisation     standardising data into one consistent form
- chaining          applying one method after another, left to right
- pipeline          an ordered sequence of cleaning steps
- return            hands the result back out of a function
- edge case         a known input the logic doesn't handle perfectly (e.g. McDonald)

---

## Interview one-liners (added Wednesday)
- "I wrote a company-name normalisation function — trims whitespace, strips legal
   suffixes like Ltd and Limited, and standardises casing."
- "Cleaning runs before dedup and CRM insert, because 'Zen Clinic Ltd' and
   'ZEN CLINIC' are the same company and need to match."
- "Clean input is what makes accurate reporting and deduplication possible."


---

## THURSDAY — Deduplication + writing CSV files

### Core idea
Duplicates are the classic CRM killer: two reps calling the same prospect,
split activity history, inflated pipeline counts, broken reporting.
Dedupe, then write the clean list out to a NEW file. Messy file in -> clean
file out. That's a tool, not a script.

### THE KEY DECISION: dedupe on DOMAIN, not company name
- Company names have unlimited variations: "Zen Clinic", "Zen Clinic Ltd",
  "ZEN CLINIC", "Zen Clinic Limited" — all one company, all different strings.
- A domain is a UNIQUE IDENTIFIER. One company, one domain. Domains don't get
  typo'd or given legal suffixes.
- So: domain dedup is reliable. Name dedup misses matches.
Interview line: "I dedupe on domain because it's a unique identifier. Names get
typo'd and formatted inconsistently; domains don't."

### A `set` = the dedup engine
A set is a collection that only holds UNIQUE items. Add the same thing twice,
it keeps one.
```python
seen = set()
seen.add("glowbeauty.co.uk")
seen.add("glowbeauty.co.uk")   # ignored, already there
```

### The dedup pattern
```python
seen_domains = set()
clean_leads = []

for lead in leads:
    domain = lead["domain"].strip().lower()

    if domain in seen_domains:                 # have I seen this before?
        print(f"DUPLICATE skipped: {lead['company_name']}")
        continue                               # throw this record away

    seen_domains.add(domain)                   # remember it

    lead["company_name"] = clean_company_name(lead["company_name"])
    lead["domain"] = domain

    clean_leads.append(lead)                   # keep it
```
CRITICAL: the `if domain in seen_domains` CHECK is what does the work. Without
it, you're just filling up a set for no reason and every lead gets kept.

### New keywords
- `set()`        collection of unique items
- `in` / `not in`  membership check — "is this already in the collection?"
- `continue`     skip the rest of this loop pass, jump to the next record
- `.lower()`     normalise case before comparing (GlowBeauty.co.uk == glowbeauty.co.uk)
- `len()`        count items — proves the dedup actually removed something

### Writing a CSV (the mirror of DictReader)
```python
with open("W2 Python for GTM Data/leads_clean.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["company_name", "domain",
                                              "industry", "country", "employees"])
    writer.writeheader()
    writer.writerows(clean_leads)
```
- `"w"` = write mode (vs `"r"` read). WARNING: overwrites the file if it exists.
- `newline=""` = Windows quirk; without it you get blank rows between every line.
- `fieldnames=[...]` = which columns, and in what order.
- `writeheader()` = writes the column-names row.
- `writerows(list)` = writes every dict as a row.

### Result
10 leads in -> 1 duplicate skipped -> 9 written to leads_clean.csv.
Logged what was dropped rather than silently removing it. A SILENT dedup is a
scary dedup; auditable is professional.

---

## FRIDAY — Missing-field validation + type conversion

### Core idea
Two silent problems remained: (1) Pure Spa had NO employee count, and (2) every
value from a CSV arrives as TEXT, not a number. Fix both, or the pipeline breaks
the moment it meets real data.

### THE BIG ONE: everything from a CSV is a STRING
When csv.DictReader reads `45` from a file, you get `"45"` — text. Python has no
idea it's meant to be a number.
```python
"45" >= 20        # TypeError — can't compare text to a number
int("45") >= 20   # True — now it's a real number
```
This is the Week 1 lesson ("45" != 45) hitting for real. My Week 1 scoring
function does `if lead["employees"] >= 20` — feed it raw CSV data and it CRASHES.
`int()` converts text to a whole number.

### Empty values are "falsy"
An empty string "" behaves like False in a check:
```python
if not lead["employees"]:      # fires when the field is empty
```

### Guard clauses — check for problems FIRST
Order inside the loop: skip duplicates -> clean -> VALIDATE -> CONVERT -> keep.
Bad records leave early via `continue` and never reach clean_leads.
```python
    lead["company_name"] = clean_company_name(lead["company_name"])
    lead["domain"] = domain

    # validate required fields
    if not lead["employees"]:
        print(f"MISSING employees: {lead['company_name']} -> sent to review")
        review_leads.append(lead)
        continue

    # convert text to number
    lead["employees"] = int(lead["employees"])

    clean_leads.append(lead)
```

### ROUTE, don't drop
Incomplete records don't vanish — they go to a REVIEW file so a human can fix
them. Two outputs:
- `leads_clean.csv`  -> ready for CRM
- `leads_review.csv` -> needs a human
Nothing disappears unaccounted for.

### The numbers must reconcile
```
Started with 10 leads
Clean: 8
Needs review: 1
(+ 1 duplicate skipped)
= 10
```
8 + 1 + 1 = 10. ALWAYS check the arithmetic. A pipeline can report confident
numbers and still be silently broken.

### Proof the conversion worked
```python
for lead in clean_leads:
    if lead["employees"] >= 20:
        print(f"{lead['company_name']}: big enough ({lead['employees']})")
```
Output:
```
Glow Beauty London: big enough (45)
Bright Smile Dental: big enough (23)
Alpine Wellness: big enough (30)
```
This comparison would have CRASHED before the int() conversion. It runs clean
now — which means my data is finally safe to score.

---

## HARD LESSON LEARNED (worth remembering)
While editing, I accidentally deleted the `if domain in seen_domains` check.
The script still RAN. No error. No red text. It just reported
"kept 10 after dedup" — a confidently wrong number — and would have pushed a
duplicate lead into the CRM.

**SILENT FAILURES ARE THE DANGEROUS ONES.** A script that crashes tells you
something is wrong. A script that quietly produces bad output doesn't. This is
exactly why I check the arithmetic (10 in -> 8 + 1 + 1 out) rather than trusting
that "it ran".

---

## QUIZ QUESTIONS + ANSWERS (Thursday–Friday)

**Q13. Why dedupe on domain instead of company name?**
A domain is a unique identifier — one company, one domain. Company names have
unlimited variations (Ltd, Limited, casing, typos) that all look different to a
computer but are the same company. Domain dedup is reliable; name dedup misses.

**Q14. What does a `set` do, and why is it the right tool for dedup?**
A set only holds unique items. Adding the same value twice keeps one. Perfect
for tracking "domains I've already seen".

**Q15. What does `continue` do?**
Skips the rest of the current loop pass and jumps to the next record. It's how
you throw a record away (duplicate, or incomplete).

**Q16. Why can't you compare `lead["employees"] >= 20` on data straight from a
CSV?**
Because a CSV gives you every value as a STRING. `"45"` is text, not a number,
and Python can't compare text to a number — it raises a TypeError. You must
convert first with `int()`.

**Q17. What does `int()` do?**
Converts a value to a whole number. `int("45")` -> `45`. Turns CSV text into
something you can do maths and comparisons on.

**Q18. Why route incomplete records to a review file instead of dropping them?**
So nothing disappears unaccounted for. A human can fix them. Auditability is
what makes it safe to run on thousands of rows — every record is either clean,
duplicate, or review.

**Q19. Why must the numbers reconcile (8 + 1 + 1 = 10)?**
Because a pipeline can run without error and still be silently broken. Checking
the arithmetic is how you catch a wrong result that didn't crash.

---

## Terminology added (Thu–Fri)
- set                collection of unique items
- in / not in        membership check
- continue           skip to the next loop pass
- len()              count items in a collection
- DictWriter         writes a list of dicts out as CSV rows
- "w" mode           write mode (overwrites!)
- newline=""         required on Windows to avoid blank rows
- int()              convert text to a whole number
- falsy              empty values ("" , 0) behave like False
- guard clause       check for problems first, before the main logic
- silent failure     code that runs fine but produces wrong output

---

## Interview one-liners (added Thu–Fri)
- "I dedupe on domain rather than company name, because domains are unique
   identifiers while names get typo'd and formatted inconsistently."
- "I log what was dropped so the process is auditable — you never want a silent
   dedup."
- "CSVs give you everything as strings, so employee counts arrive as text and
   would crash a numeric comparison. I convert types explicitly."
- "I validate required fields before processing and route incomplete records to
   a review file rather than letting one bad row kill the run."
- "Every record is accounted for — clean, duplicate, or review. That
   auditability is what makes it safe to run on thousands of rows."