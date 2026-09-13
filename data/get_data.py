import requests
import pandas as pd
import pprint
import json

params = {
    "scientificName": "Agaricomycetes",
    "country": "GB",
    "hasCoordinate": "true",
    "limit": 300,
    "offset": 0
}

response = requests.get(
    "https://api.gbif.org/v1/occurrence/search",
    # params=params
)

data = response.json()["results"]

records = []

for item in data:
    records.append({
        "species": item.get("species"),
        "scientific_name": item.get("scientificName"),
        "accepted_name": item.get("acceptedScientificName"),
        "genus": item.get("genus"),
        "family": item.get("family"),
        "event_date": item.get("eventDate"),
        "year": item.get("year"),
        "month": item.get("month"),
        "latitude": item.get("decimalLatitude"),
        "longitude": item.get("decimalLongitude"),
        "country": item.get("country"),
        "locality": item.get("locality"),
        "habitat": item.get("habitat"),
        "basis_of_record": item.get("basisOfRecord"),
        "license": item.get("license"),
        "dataset": item.get("datasetName")
    })

response.raise_for_status()

gbif_data = response.json()
records = gbif_data["results"]

print(json.dumps(records[:3], indent=2, ensure_ascii=False))

agari = "https://api.gbif.org/v1/species/match?name=Agaricomycetes&rank=class"
lecano = "https://api.gbif.org/v1/species/match?name=Lecanoromycetes&rank=class"
pezizo = "https://api.gbif.org/v1/species/match?name=Pezizomycetes&rank=class"