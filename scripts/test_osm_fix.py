#!/usr/bin/env python
"""Test OSM collector fix"""

from pipelines.ingestion.osm_collector_real import OSMCollectorReal

collector = OSMCollectorReal()
print("Testing OSM collection for Hanoi restaurants...")

results = collector.collect(
    city='hanoi',
    category='restaurant',
    lat=21.0278,
    lng=105.8342,
    radius=5000
)

print(f"Results: {len(results)} POIs")
if results:
    print(f"Sample: {results[0].get('name', 'N/A')}")
    print("✅ OSM collector is WORKING!")
else:
    print("⚠️ No results")
