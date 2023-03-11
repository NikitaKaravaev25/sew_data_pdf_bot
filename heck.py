import re

pattern = r"\d{2}\.\d{10}\.\d{4}\.\d{2}"
text = "40.8109600003.0001.09"

if re.match(pattern, text):
    print("Yes")
else:
    print("No")