import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DATA_GOV_API_KEY")

url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

params = {
    "api-key": api_key,
    "format": "json",
    "limit": 1,
}

start = time.time()

try:
    response = requests.get(url, params=params, timeout=(10, 15))

    print("Status:", response.status_code)
    print("Time:", round(time.time() - start, 2), "seconds")
    print(response.text[:1000])

except requests.exceptions.RequestException as error:
    print("Request failed:", error)