import requests

def fetch_post(post_id):
    url = f"https://jsonplaceholder.typicode.com/posts/{post_id}"
    response = requests.get(url)
    print(f"Post {post_id} -> status {response.status_code}")

    if not response.ok:                       # 1. cleaner status check
        print(f"  Skipping — bad response, moving on")
        return

    try:                                      # 3. guard the parse itself
        data = response.json()
    except ValueError:
        print("  Response wasn't valid JSON — skipping")
        return

    title = data.get('title', 'NO TITLE')     # Part B safety, still here
    author = data.get('author', 'NO AUTHOR')
    print(f"  Title: {title}")
    print(f"  Author: {author}")

fetch_post(1)
fetch_post(9999)