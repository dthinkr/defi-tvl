import requests
import sys
from io import StringIO


BASE_URL = "http://127.0.0.1:8000"

url = f"{BASE_URL}/unique-protocols"

response = requests.get(url)

if response.status_code == 200:
    csv_data = StringIO(response.text)
    sys.stdout.write(csv_data.getvalue())
else:
    print(f"Failed to fetch data. Status code: {response.status_code}")