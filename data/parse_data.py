import os
import zipfile
import csv
from pymongo import MongoClient

# env vars
GBIF_API = os.getenv("GBIF_API")
MONGODB_URI = os.getenv("MONGODB_URI")

## Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client["the_shroomz"]
collection = db["trash"]

columns = ["_id","key", "basisOfRecord", "occurrenceStatus", "lifeStage", "classifications",
           "taxonKey", "kingdomKey", "phylumKey", "classKey", "orderKey", "familyKey", "genusKey",
           "speciesKey", "scientificName", "acceptedScientificName", "acceptedTaxonKey", 
           "kingdom", "phylum", "class", "order", "family", "genus", "species",
           "genericName", "taxonomicStatus", "iucnRedListCategory", "dateIdentified", "elevation",
           "depth", "continent", "stateProvince", "waterBody", "higherGeography", "eventDate",
           "references", "organismQuantity", "sampleSizeUnit", "sampleSizeValue", "relativeOrganismQuantity",
           "media", "facts", "identifiedBy", "samplingProtocol", "country", "relations"
           ]
           
CONTINENTS = ["EUROPE"]
latest_by_species = {}

with zipfile.ZipFile("gbif_download.zip") as zf:
    csv_name = [n for n in zf.namelist() if n.endswith(".csv")][0]

    with zf.open(csv_name) as f:
        reader = csv.DictReader(
            (line.decode("utf-8") for line in f), delimiter="\t"
        )

        print(f"Reading {csv_name} and keeping latest record per species...", flush=True)
        latest_by_species = {}

        for row_num, row in enumerate(reader, start=1):
            species_key = row.get("speciesKey")
            event_date = row.get("eventDate")

            if not species_key or not event_date:
                continue  # skip rows we can't compare/group

            existing = latest_by_species.get(species_key)
            if existing is None or event_date > existing["eventDate"]:
            #     for key in list(row.keys()):
            #         if key not in columns:
            #             del row[key]
                latest_by_species[species_key] = row

            if row_num % 10000 == 0:
                print(f"Scanned {row_num} rows, {len(latest_by_species)} species so far...", flush=True)

        batch = list(latest_by_species.values())
        if batch:
            collection.insert_many(batch)
        print(f"Inserted {len(batch)} deduped records (one per species). Done.", flush=True)

print("DONE")





            