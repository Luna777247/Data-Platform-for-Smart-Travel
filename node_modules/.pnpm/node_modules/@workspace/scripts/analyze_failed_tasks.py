#!/usr/bin/env python
"""Analyze failed tasks in mass collection"""

from pymongo import MongoClient

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

# Expected tasks: 8 cities × 9 categories × 9 grid = 648
CITIES = ['hanoi', 'hcm', 'danang', 'haiphong', 'cantho', 'nhatrang', 'dalat', 'hue']
CATEGORIES = ['restaurant', 'cafe', 'hotel', 'tourist_attraction', 'shopping_mall', 
              'supermarket', 'bar', 'spa', 'gym']

print("=" * 60)
print("🔍 FAILED TASKS ANALYSIS")
print("=" * 60)

# Check actual collected data by city-category combination
print("\n📊 Checking missing data...")
failed_combinations = []

for city in CITIES:
    for category in CATEGORIES:
        # Count records for this city-category
        count = db.bronze_records.count_documents({
            'city': city,
            'category': category,
            '_job_id': 'mass_20260510_004405'
        })
        
        # Should have ~9 grid points × up to 20 POIs = ~180 max
        # But if count is 0 or very low, likely failed
        if count == 0:
            failed_combinations.append((city, category, count))
            print(f"  ❌ {city}/{category}: {count} POIs (LIKELY FAILED)")
        elif count < 50:  # Suspiciously low
            print(f"  ⚠️  {city}/{category}: {count} POIs (LOW)")

print(f"\n📍 Potentially failed combinations: {len(failed_combinations)}")
for city, cat, cnt in failed_combinations[:10]:
    print(f"  - {city}/{cat}: {cnt}")

# Check by city totals
print("\n📍 City totals:")
for city in CITIES:
    total = db.bronze_records.count_documents({
        'city': city,
        '_job_id': 'mass_20260510_004405'
    })
    expected = 9 * 9 * 20  # 9 categories × 9 grid × ~20 POIs
    status = "✅" if total > 1000 else "⚠️" if total > 500 else "❌"
    print(f"  {status} {city}: {total} POIs")

# Check by category totals
print("\n📁 Category totals:")
for cat in CATEGORIES:
    total = db.bronze_records.count_documents({
        'category': cat,
        '_job_id': 'mass_20260510_004405'
    })
    expected = 8 * 9 * 20  # 8 cities × 9 grid × ~20 POIs
    print(f"  {cat}: {total} POIs")

client.close()
print("\n" + "=" * 60)
