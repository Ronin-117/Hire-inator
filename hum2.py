import requests

url = "https://docs.humanizeai.pro/_mock/openapi/"

payload = {
  "text": "Artificial intelligence has transformed the way we work, communicate, and solve problems. While it's efficient and powerful, its tone often lacks the warmth and nuance of human expression.",
  "id":"1234567890"
}

headers = {
  "Content-Type": "application/json",
  "x-api-key": "sk_wbcrlxr1srey57ccvvtq"
}

response = requests.post(url, json=payload, headers=headers)

data = response.json()
print(data)