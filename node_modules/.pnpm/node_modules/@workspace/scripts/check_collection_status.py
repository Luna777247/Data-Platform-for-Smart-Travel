#!/usr/bin/env python
"""Check collection progress"""

from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

# Check current bronze count
total = db.bronze_records.count_documents({})
google_real = db.bronze_records.count_documents({'_source': 'google_real'})

print('=' * 60)
print('📊 COLLECTION PROGRESS')
print('=' * 60)
print(f'Total Bronze: {total} records')
print(f'Google Real: {google_real} records')
print()

# Check by city
print('📍 By City:')
cities = ['hanoi', 'hcm', 'danang', 'haiphong', 'cantho', 'nhatrang', 'dalat', 'hue']
for city in cities:
    count = db.bronze_records.count_documents({'city': city})
    if count > 0:
        print(f'  {city}: {count} POIs')

print()
print('📁 By Category:')
pipeline = [{'$group': {'_id': '$category', 'count': {'$sum': 1}}}]
cats = list(db.bronze_records.aggregate(pipeline))
for cat in sorted(cats, key=lambda x: -x['count'])[:10]:
    print(f"  {cat['_id']}: {cat['count']}")

# Check latest job
job = db.collection_jobs.find_one(sort=[('created_at', -1)])
if job:
    print()
    print(f"💾 Latest Job: {job.get('job_id', 'N/A')}")
    print(f"  Status: {job.get('status', 'N/A')}")
    stats = job.get('stats', {})
    print(f"  Completed Tasks: {stats.get('completed', 0)}")
    print(f"  Failed Tasks: {stats.get('failed', 0)}")
    print(f"  Total POIs: {stats.get('total_records', 0)}")

client.close()
print('=' * 60)
