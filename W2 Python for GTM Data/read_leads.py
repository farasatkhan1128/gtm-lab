import csv

with open("Week 2/leads.csv", "r") as file:
    reader = csv.DictReader(file)
    leads = list(reader)


for lead in leads:
    if lead["country"] == "United Kingdom" and lead["industry"] == "Beauty":
        print(f"UK BEAUTY LEAD: {lead['company_name']}")
    else:
        print(f"skip: {lead['company_name']}")
