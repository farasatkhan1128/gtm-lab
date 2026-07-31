import time

# ─── STAND-IN: pretend this is a real paginated API endpoint ───
# It holds 23 companies and hands them back 10 at a time.
_ALL_COMPANIES = [{"id": i, "name": f"Company {i}"} for i in range(1, 24)]  # 23 fake companies

def get_page(page_number, page_size=10):
    """Returns one page of results, like a real API would."""
    start = (page_number - 1) * page_size
    end = start + page_size
    rows = _ALL_COMPANIES[start:end]
    return {
        "page": page_number,
        "rows": rows,
        "has_more": end < len(_ALL_COMPANIES),   # is there a next page?
    }
# ───────────────────────────────────────────────────────────────


# ─── THE PART THAT MATTERS: loop through every page ───
all_rows = []
page = 1

while True:
    print(f"Fetching page {page}...")
    response = get_page(page)          # in production: requests.get(url, params={"page": page})

    all_rows.extend(response["rows"])  # add this page's rows to the full list
    print(f"  got {len(response['rows'])} rows (running total: {len(all_rows)})")

    if not response["has_more"]:       # stop condition: no more pages
        break

    page += 1                          # otherwise, go to the next page
    time.sleep(0.3)                    # pace it, same as any batch of API calls

print(f"\nDone. Pulled {len(all_rows)} companies across {page} pages.")