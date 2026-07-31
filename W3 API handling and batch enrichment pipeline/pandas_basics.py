import pandas as pd

# A realistic company dataset — the shape enrichment gives you,
# with the fields that matter for ICP scoring.
companies = [
    {"company": "Stripe",   "industry": "Fintech",    "country": "United States", "employees": 8000},
    {"company": "Monzo",    "industry": "Fintech",    "country": "United Kingdom", "employees": 2500},
    {"company": "Canva",    "industry": "Design",     "country": "Australia",     "employees": 4000},
    {"company": "Gusto",    "industry": "HR Software", "country": "United States", "employees": 3000},
    {"company": "Deel",     "industry": "HR Software", "country": "United States", "employees": 3500},
    {"company": "Tide",     "industry": "Fintech",    "country": "United Kingdom", "employees": 1800},
    {"company": "Figma",    "industry": "Design",     "country": "United States", "employees": 1200},
    {"company": "Pleo",     "industry": "Fintech",    "country": "Denmark",       "employees": 900},
    {"company": "Remote",   "industry": "HR Software", "country": "United States", "employees": 1400},
    {"company": "Airtable", "industry": "Software",   "country": "United States", "employees": 1000},
]

# Turn the list of dicts into a DataFrame (a table).
df = pd.DataFrame(companies)

# --- three ways to look at a DataFrame ---
print("=== The whole table ===")
print(df)

print("\n=== Just the first 3 rows (.head) ===")
print(df.head(3))

print("\n=== Shape: (rows, columns) ===")
print(df.shape)

print("\n=== Column names ===")
print(df.columns.tolist())

print("\n=== Quick stats on number columns (.describe) ===")
print(df.describe())
# ─── FILTERING: keep only rows matching a condition ───

print("\n=== Companies with 3000+ employees ===")
big = df[df["employees"] >= 3000]
print(big)

print("\n=== Only Fintech companies ===")
fintech = df[df["industry"] == "Fintech"]
print(fintech)

print("\n=== Fintech AND 2000+ employees (two conditions) ===")
big_fintech = df[(df["industry"] == "Fintech") & (df["employees"] >= 2000)]
print(big_fintech)

print("\n=== How many US companies? ===")
us_count = len(df[df["country"] == "United States"])
print(f"{us_count} US companies")
# ─── GROUPING: collapse rows into per-category summaries ───

print("\n=== How many companies per industry? ===")
per_industry = df.groupby("industry").size()
print(per_industry)

print("\n=== Average employees per industry ===")
avg_emp = df.groupby("industry")["employees"].mean()
print(avg_emp)

print("\n=== How many companies per country? ===")
per_country = df.groupby("country").size()
print(per_country)

print("\n=== Total employees per country ===")
total_emp = df.groupby("country")["employees"].sum()
print(total_emp)