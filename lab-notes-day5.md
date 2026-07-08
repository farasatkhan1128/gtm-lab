# Self-Hosted AI GTM Lab — Notes

## Day 5 — The ICP Scoring Engine (8 Jul 2026)

### Core idea of the day
Turned a single if-statement into a real SCORING FUNCTION that takes any
lead and returns the target output shape:
  { "icp_score": 85, "tier": "Tier 1", "reason": "..." }
This is the heart of the whole portfolio project and the most
interview-relevant piece.

### What a function is
A reusable machine: data goes in, a result comes out.
  def score_lead(lead):     # define a function called score_lead, input = lead
      ...
      return { ... }         # hand back the result
- def = "define a function"
- (lead) = the input it expects
- return = what it hands back

### The pattern: accumulate a score + collect reasons
  score = 0
  reasons = []
  if <rule passes>:
      score += 25              # add points (same as score = score + 25)
      reasons.append("why")    # record WHY, so the output explains itself

### My scoring rules (weights are deliberate and defensible)
  Rule 1: country == "United Kingdom"  -> +25  "UK market"
  Rule 2: industry == "Beauty"         -> +30  "target industry (beauty)"
  Rule 3: employees >= 20              -> +30  "suitable team size"

### Tiering: turn the number into an action
  if score >= 80:   tier = "Tier 1"
  elif score >= 50: tier = "Tier 2"
  else:             tier = "Tier 3"
- elif = "else if" — only checked if the previous condition failed
- ", ".join(reasons) glues the list into one sentence:
    ["UK market", "suitable team size"] -> "UK market, suitable team size"

### The full function
```python
def score_lead(lead):
    score = 0
    reasons = []

    if lead["country"] == "United Kingdom":
        score += 25
        reasons.append("UK market")

    if lead["industry"] == "Beauty":
        score += 30
        reasons.append("target industry (beauty)")

    if lead["employees"] >= 20:
        score += 30
        reasons.append("suitable team size")

    if score >= 80:
        tier = "Tier 1"
    elif score >= 50:
        tier = "Tier 2"
    else:
        tier = "Tier 3"

    reason = ", ".join(reasons)

    return {
        "icp_score": score,
        "tier": tier,
        "reason": reason
    }
```

### Proof it discriminates (tested on 2 leads)
Strong lead (Glow Beauty London, UK, Beauty, 45 staff):
  {'icp_score': 85, 'tier': 'Tier 1', 'reason': 'UK market, target industry
   (beauty), suitable team size'}
Weak lead (Tiny Tools Ltd, Germany, Manufacturing, 5 staff):
  {'icp_score': 0, 'tier': 'Tier 3', 'reason': ''}
A good engine SEPARATES leads. Empty reason on the weak lead is correct —
no rules passed, so there's nothing to explain.

### The bug I hit and fixed (important lesson)
Got "'return' outside function". Cause: the tier/reason/return block was at
the far-left margin, i.e. OUTSIDE the function. return only works INSIDE a
function. Fix: indent the whole block one level so it sits inside def.
LESSON: In Python, INDENTATION defines what belongs to the function.
  left margin      = outside the function
  4 spaces in      = inside the function
  8 spaces in      = inside an if that's inside the function

### Why the REASON matters as much as the score (interview gold)
A salesperson can't act on "85". But "UK beauty company, right size" tells
them how to pitch. Scoring on transparent, weighted RULES (not gut feel) is
the difference between engineering and vibes — and the weights are
defensible when an interviewer challenges them.

### Interview explanation (say out loud)
"I built a weighted ICP scoring function. It takes a lead, runs transparent
rules — market, industry, team size, each worth defined points — and returns
a score, a tier, and a human-readable reason. The reason matters as much as
the score: a salesperson can't act on '85', but 'UK beauty company, right
size' tells them how to pitch. The weights are deliberate and defensible,
which is the difference between scoring on rules versus scoring on vibes."

### Why this matters for GTM Engineering
Every GTM team argues about "what's a good lead". This encodes that judgement
into transparent rules instead of gut feel. Maps directly to my TikTok work
scoring and routing leads. Next: feed REAL csv data (Week 2) through this
engine after cleaning and deduping.
