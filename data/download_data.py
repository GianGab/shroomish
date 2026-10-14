import requests
import os

GBIF_EMAIL = os.getenv("GBIF_EMAIL")
GBIF_USERNAME = os.getenv("GBIF_USERNAME")
GBIF_PASSWORD = os.getenv("GBIF_PASSWORD")

print(GBIF_EMAIL)
print(GBIF_USERNAME)
print(GBIF_PASSWORD)

GBIF_API = "https://api.gbif.org/v1"
CLASS_KEYS = [186, 316, 180, 313, 314, 10874653]

body = {
    "creator": GBIF_USERNAME,
    "notificationAddresses": [GBIF_EMAIL],
    "format": "SIMPLE_CSV",
    "predicate": {
        "type": "and",
        "predicates": [
            {"type": "in", "key": "TAXON_KEY", "values": [str(key) for key in CLASS_KEYS]},
            {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
            {"type": "greaterThanOrEquals", "key": "YEAR", "value": "2010"},
            {"type": "lessThanOrEquals", "key": "YEAR", "value": "2026"},
        ]
    }
}

download_key = requests.post(
    f"{GBIF_API}/occurrence/download/request",
    json=body,
    auth=(GBIF_USERNAME, GBIF_PASSWORD),
)

print(download_key.status_code)
print(download_key.text)  # this is your download key, e.g. "0123456-987654321"

import time

download_key = download_key.text.strip().strip('"')

status_url = f"{GBIF_API}/occurrence/download/{download_key}"

while True:
    status_resp = requests.get(status_url)
    status = status_resp.json()["status"]
    print(status)
    if status == "SUCCEEDED":
        break
    if status in ("KILLED", "FAILED", "CANCELLED"):
        raise RuntimeError(f"Download failed with status: {status}")
    time.sleep(30)

zip_url = f"{GBIF_API}/occurrence/download/request/{download_key}.zip"
zip_resp = requests.get(zip_url)

with open("gbif_download.zip", "wb") as f:
    f.write(zip_resp.content)



zip_url = f"{GBIF_API}/occurrence/download/request/{download_key}.zip"

zip_resp = requests.get(zip_url, stream=True)
zip_resp.raise_for_status()

with open("gbif_download.zip", "wb") as f:
    for chunk in zip_resp.iter_content(chunk_size=8192):
        f.write(chunk)

print("Download saved to gbif_download.zip")