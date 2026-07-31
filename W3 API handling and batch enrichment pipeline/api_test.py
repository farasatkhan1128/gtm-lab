import requests

# GET request to a free public API
response = requests.get("https://jsonplaceholder.typicode.com/users/1")

# check the status code first — always
print("Status code:", response.status_code)

# turn the JSON response into a Python dictionary
data = response.json()

# read fields from it
print("Name:", data["name"])
print("Email:", data["email"])
print("Company:", data["company"]["name"])


response = requests.get("https://jsonplaceholder.typicode.com/users/9999")
print("Status code:", response.status_code)