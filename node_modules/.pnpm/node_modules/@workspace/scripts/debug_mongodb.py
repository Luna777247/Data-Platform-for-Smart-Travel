#!/usr/bin/env python
"""Debug MongoDB document structure"""
from pymongo import MongoClient

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

# Get one document from gold_master_pois
print("Sample document from gold_master_pois:")
doc = db.gold_master_pois.find_one({})
if doc:
    print(f"Type: {type(doc)}")
    print(f"Keys: {list(doc.keys())}")
    print(f"Has created_at: {'created_at' in doc}")
    print(f"Has updated_at: {'updated_at' in doc}")
    print(f"Has _enriched_at: {'_enriched_at' in doc}")
    print(f"Has _processed_at: {'_processed_at' in doc}")
    print(f"\nFull doc (first 5 keys):")
    for i, (k, v) in enumerate(doc.items()):
        if i < 5:
            print(f"  {k}: {type(v).__name__} = {v}")
else:
    print("No documents found!")

client.close()
