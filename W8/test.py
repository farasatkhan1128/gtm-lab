date = "2026-04-15"
print(date[-2:])










text = " £Engineering " . strip(" £")
print(text)


import re

raw = "968-Maria, ( D@t@ Engineer );; 27y  "

# Step 1 — fix the noise: @ -> a, and lowercase everything
s = raw.replace("@", "a").lower()
# s is now: "968-maria, ( data engineer );; 27y  "

# Step 2 — pull out each piece by its landmark
name = re.search(r'-\s*([a-z]+)', s).group(1)          # word after the dash
role = re.search(r'\(([^)]+)\)', s).group(1).strip()   # text inside ( )
age  = re.search(r'(\d+)\s*y', s).group(1)             # digits before 'y'

# Step 3 — build the summary
print(f"name: {name} | role: {role} | age: {age}")










phone = "+441234567890"
print(phone.endswith("7890"))  # True
print("@" in phone)  # True


phone1 = "+441234567890"
print(phone1[3:])




X= "32"
print(type(X))  # <class 'str'>
x = int(X)
print(x * 3) # 96
