import requests
import os

url = "http://127.0.0.1:8000/upload"
file_path = "test_catalog.pdf"

if not os.path.exists(file_path):
    with open(file_path, "wb") as f:
        f.write(b"%PDF-1.4 test content")

with open(file_path, "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
