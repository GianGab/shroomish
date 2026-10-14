import requests
import pandas as pd
import pprint
import json
from pymongo import MongoClient
import os
import time

# env vars
GBIF_API = os.getenv("GBIF_API")
MONGODB_URI = os.getenv("MONGODB_URI")

## Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client["the_shroomz"]
collection = db["trash"]

MUSHROOM_CLASSES = ["Agaricomycetes", "Pezizomycetes"]
LICHEN_CLASSES = ["Lecanoromycetes", "Arthoniomycetes", "Lichinomycetes", "Coniocybomycetes"]
ALL_CLASSES = MUSHROOM_CLASSES + LICHEN_CLASSES
CLASS_KEYS = [186, 316, 180, 313, 314, 10874653]

# CONTINENTS = [
#     "AFRICA", "ANTARCTICA", "ASIA", "EUROPE",
#     "NORTH_AMERICA", "OCEANIA", "SOUTH_AMERICA",
# ]
CONTINENTS = ["EUROPE"]

# Stay comfortably clear of the ~10,000 deep-pagination cliff
SAFE_OFFSET_LIMIT = 9_000
YEARS = range(2005, 2027)  # adjust start year to taste

columns = ["_id","key", "basisOfRecord", "occurrenceStatus", "lifeStage", "classifications",
           "taxonKey", "kingdomKey", "phylumKey", "classKey", "orderKey", "familyKey", "genusKey",
           "speciesKey", "scientificName", "acceptedScientificName", "acceptedTaxonKey", 
           "kingdom", "phylum", "class", "order", "family", "genus", "species",
           "genericName", "taxonomicStatus", "iucnRedListCategory", "dateIdentified", "elevation",
           "depth", "continent", "stateProvince", "waterBody", "higherGeography", "eventDate",
           "references", "organismQuantity", "sampleSizeUnit", "sampleSizeValue", "relativeOrganismQuantity",
           "media", "facts", "identifiedBy", "samplingProtocol", "country", "relations"
           ]


def page_through(params, grouped, page_size, max_retries):
    """Page through one params dict until endOfRecords or the safe offset limit."""
    offset = 0
    while True:
        params["offset"] = offset
        params["limit"] = page_size
        print(f"  Fetching {params} ...", flush=True)

        for attempt in range(max_retries):
            try:
                start = time.time()
                response = requests.get(f"{GBIF_API}/occurrence/search", params=params, timeout=30)
                print(f"    status {response.status_code}, took {time.time() - start:.1f}s", flush=True)
                if response.status_code == 429:
                    wait = 2 ** attempt
                    print(f"    rate limited, waiting {wait}s...", flush=True)
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                break
            except requests.exceptions.Timeout:
                wait = 2 ** attempt
                print(f"    timed out, retrying in {wait}s... (attempt {attempt + 1}/{max_retries})", flush=True)
                time.sleep(wait)
        else:
            raise RuntimeError(f"Gave up on {params} after {max_retries} attempts")

        payload = response.json()

        if offset == 0 and payload["count"] > SAFE_OFFSET_LIMIT and "year" not in params:
            # This slice is too big to page safely -- signal caller to split by year instead
            return payload["count"]

        for record in payload["results"]:
            location = (record.get("decimalLatitude"), record.get("decimalLongitude"))
            grouped.setdefault(location, []).append(record)

        offset += page_size

        if payload["endOfRecords"] or offset + page_size > SAFE_OFFSET_LIMIT:
            break

        time.sleep(0.2)

    return None  # slice was handled fully, no further split needed


def fetch_shroomies_by_location(class_keys, page_size=300, max_retries=5):
    grouped = {}

    print("Looping through class keys...", flush=True)
    for class_key in class_keys:
        for continent in CONTINENTS:
            base_params = {
                "taxonKey": class_key,
                "continent": continent,
                "hasCoordinate": "true",
                "hasGeospatialIssue": "false",
            }

            too_big = page_through(dict(base_params), grouped, page_size, max_retries)

            if too_big is not None:
                print(f"  classKey {class_key} / {continent}: {too_big} records, splitting by year", flush=True)
                for year in YEARS:
                    year_params = dict(base_params)
                    year_params["year"] = year
                    page_through(year_params, grouped, page_size, max_retries)

    print(f"Fetched {sum(len(v) for v in grouped.values())} records across {len(grouped)} unique locations.", flush=True)
    return grouped


grouped_shroomies = fetch_shroomies_by_location(CLASS_KEYS)
for shroom in grouped_shroomies:
    for record in grouped_shroomies[shroom]:
        for key in list(record.keys()):
            if key not in columns:
                del record[key]
        collection.insert_one(record)

print(f"Inserted {collection.count_documents({})} records into MongoDB.", flush=True)


## PROBLEM: just resets all the time