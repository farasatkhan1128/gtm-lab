leads = [
    {
        "company_name": "Glow Beauty London",
        "domain": "glowbeauty.co.uk",
        "industry": "Beauty",
        "country": "United Kingdom",
        "employees": 45
    },
    {
        "company_name": "Fresh Hair Studio",
        "domain": "freshhairstudio.co.uk",
        "industry": "Hair Salon",
        "country": "United Kingdom",
        "employees": 8
    },
    {
        "company_name": "Zen Clinic",
        "domain": "zenclinic.co.uk",
        "industry": "Med Spa",
        "country": "United Kingdom",
        "employees": 12
    }
]

for lead in leads:
    print(f"{lead['company_name']} is a {lead['industry']} business with {lead['employees']} employees.")