#!/usr/bin/env python
"""Check data layer status after processing"""
from pymongo import MongoClient

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

print('='*60)
print('📊 LAYER STATUS AFTER PROCESSING')
print('='*60)

bronze = db.bronze_records.count_documents({})
silver = db.silver_places.count_documents({})
gold = db.gold_master_pois.count_documents({})

print(f'\nBronze: {bronze:,} records')
print(f'Silver: {silver:,} records')
print(f'Gold:   {gold:,} records')

print()
print('🎯 Processing Results:')
if bronze > 0:
    print(f'  Silver: {silver}/{bronze} bronze records ({silver/bronze*100:.1f}%)')
if silver > 0:
    print(f'  Gold:   {gold}/{silver} silver records ({gold/silver*100:.1f}%)')

if gold > 0:
    print()
    print('📍 Gold POIs by city:')
    cities = list(db.gold_master_pois.aggregate([{'$group': {'_id': '$city', 'count': {'$sum': 1}}}]))
    for c in sorted(cities, key=lambda x: -x['count'])[:10]:
        print(f'  {c["_id"]}: {c["count"]}')

client.close()
print('='*60)
