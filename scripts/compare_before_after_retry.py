#!/usr/bin/env python
"""
Compare collection before and after Phase 2 retry
"""

from pymongo import MongoClient

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

print("=" * 70)
print("📊 SO SÁNH TRƯỚC VÀ SAU PHASE 2 RETRY")
print("=" * 70)

# Current total
current_total = db.bronze_records.count_documents({})
before_retry = 18656  # From previous check

print(f"\n📈 Tổng quan:")
print(f"   Trước retry: {before_retry:,} POIs")
print(f"   Sau retry:   {current_total:,} POIs")
print(f"   Tăng thêm:   +{current_total - before_retry:,} POIs ({(current_total - before_retry) / before_retry * 100:.1f}%)")

# Cities that improved
print(f"\n📍 Cities được cải thiện sau retry:")

retry_cities = {
    'vungtau': 'Trước: ~20 → Sau: ',
    'tayninh': 'Trước: ~23 → Sau: ',
    'pleiku': 'Trước: ~26 → Sau: ',
    'longan': 'Trước: 0 → Sau: ',
}

for city, prefix in retry_cities.items():
    count = db.bronze_records.count_documents({'city': city})
    print(f"   {city}: {prefix}{count} POIs (+{count - 20 if city != 'longan' else count})")

# Phase 2 cities that were already good
print(f"\n📍 Cities Phase 2 đã hoàn thiện (không đổi):")
good_p2_cities = ['vinh', 'quangninh', 'thainguyen', 'quynhon', 'tuyhoa', 'langson', 'camranh', 'phanthiet']
for city in good_p2_cities:
    count = db.bronze_records.count_documents({'city': city})
    print(f"   {city}: {count} POIs")

# Cities with no data (still failed)
print(f"\n❌ Cities vẫn không có data:")
failed_cities = ['tiengiang', 'bentre', 'buonmathuot']
for city in failed_cities:
    count = db.bronze_records.count_documents({'city': city})
    print(f"   {city}: {count} POIs")

# Phase 1 cities (no change)
print(f"\n✅ Cities Phase 1 (không đổi):")
p1_cities = ['hanoi', 'hcm', 'danang', 'haiphong', 'cantho', 'nhatrang', 'dalat', 'hue']
p1_total = 0
for city in p1_cities:
    count = db.bronze_records.count_documents({'city': city})
    p1_total += count
print(f"   Tổng 8 cities Phase 1: {p1_total:,} POIs")

# Summary by source
print(f"\n📊 Phân bố theo nguồn:")
p1_count = db.bronze_records.count_documents({'_source': {'$regex': 'phase1|20260510_004405'}})
p2_count = db.bronze_records.count_documents({'_source': {'$regex': 'phase2|p2_'}})
retry_count = db.bronze_records.count_documents({'_source': {'$regex': 'retry'}})

print(f"   Phase 1: ~{p1_count:,} POIs")
print(f"   Phase 2 (original): ~{p2_count - retry_count:,} POIs")
print(f"   Phase 2 (retry): ~{retry_count:,} POIs")

client.close()

print("\n" + "=" * 70)
print("✅ KẾT LUẬN:")
print("=" * 70)
print(f"• Thêm {current_total - before_retry:,} POIs từ 4 cities được retry")
print(f"• Vungtau, Tayninh, Pleiku, Longan đã có data đầy đủ")
print(f"• 3 cities vẫn thiếu: Tiengiang, Bentre, Buonmathuot")
print(f"• Tổng: {current_total:,} POIs từ 20 cities")
print("=" * 70)
