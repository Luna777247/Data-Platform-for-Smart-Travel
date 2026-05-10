#!/usr/bin/env python
"""
Data Analysis - Pre-Processing Report
=====================================
Phân tích dữ liệu Bronze trước khi chạy Silver → Gold processing
"""

from pymongo import MongoClient
from collections import Counter
import statistics

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

print("=" * 80)
print("📊 DATA ANALYSIS - PRE-PROCESSING REPORT")
print("=" * 80)

# 1. TỔNG QUAN
print("\n📈 TỔNG QUAN")
print("-" * 80)
total = db.bronze_records.count_documents({})
print(f"Tổng số records: {total:,}")

# By source
sources = list(db.bronze_records.aggregate([
    {'$group': {'_id': '$_source', 'count': {'$sum': 1}}}
]))
print(f"\nTheo nguồn:")
for src in sorted(sources, key=lambda x: -x['count']):
    pct = src['count'] / total * 100
    print(f"  {src['_id'] or 'N/A'}: {src['count']:,} ({pct:.1f}%)")

# 2. PHÂN TÍCH THEO CITY
print("\n\n🏙️ PHÂN TÍCH THEO THÀNH PHỐ")
print("-" * 80)
cities = list(db.bronze_records.aggregate([
    {'$group': {'_id': '$city', 'count': {'$sum': 1}}}
]))
cities = sorted(cities, key=lambda x: -x['count'])

print(f"Tổng số cities: {len(cities)}")
print(f"\nTop 10 cities nhiều POIs nhất:")
for i, city in enumerate(cities[:10], 1):
    pct = city['count'] / total * 100
    print(f"  {i}. {city['_id']}: {city['count']:,} POIs ({pct:.1f}%)")

print(f"\nCities ít POIs nhất:")
for city in cities[-5:]:
    pct = city['count'] / total * 100
    print(f"  {city['_id']}: {city['count']:,} POIs ({pct:.1f}%)")

# Stats
city_counts = [c['count'] for c in cities]
print(f"\n📊 Thống kê phân bố:")
print(f"  Trung bình: {statistics.mean(city_counts):.0f} POIs/city")
print(f"  Median: {statistics.median(city_counts):.0f}")
print(f"  Min: {min(city_counts)}")
print(f"  Max: {max(city_counts)}")
print(f"  Std dev: {statistics.stdev(city_counts):.0f}")

# 3. PHÂN TÍCH THEO CATEGORY
print("\n\n📁 PHÂN TÍCH THEO DANH MỤC")
print("-" * 80)
categories = list(db.bronze_records.aggregate([
    {'$group': {'_id': '$category', 'count': {'$sum': 1}}}
]))
categories = sorted(categories, key=lambda x: -x['count'])

print(f"Tổng số categories: {len(categories)}")
print(f"\nPhân bố:")
for cat in categories:
    pct = cat['count'] / total * 100
    bar = '█' * int(pct / 2)
    print(f"  {cat['_id'] or 'N/A':20} {cat['count']:>6,} ({pct:>5.1f}%) {bar}")

# 4. PHÂN TÍCH QUALITY
print("\n\n⭐ PHÂN TÍCH CHẤT LƯỢNG DATA")
print("-" * 80)

# Rating stats
rated_count = db.bronze_records.count_documents({'rating': {'$exists': True, '$ne': None}})
unrated_count = total - rated_count

print(f"POIs có rating: {rated_count:,} ({rated_count/total*100:.1f}%)")
print(f"POIs không có rating: {unrated_count:,} ({unrated_count/total*100:.1f}%)")

# Rating distribution
ratings = list(db.bronze_records.find({'rating': {'$exists': True, '$ne': None}}, {'rating': 1}))
rating_values = [r['rating'] for r in ratings if r['rating'] is not None]

if rating_values:
    print(f"\n📊 Thống kê rating:")
    print(f"  Trung bình: {statistics.mean(rating_values):.2f}")
    print(f"  Median: {statistics.median(rating_values):.2f}")
    print(f"  Min: {min(rating_values):.1f}")
    print(f"  Max: {max(rating_values):.1f}")
    
    # Rating distribution
    rating_dist = Counter(round(r, 0) for r in rating_values)
    print(f"\nPhân bố rating:")
    for rating in sorted(rating_dist.keys()):
        count = rating_dist[rating]
        pct = count / len(rating_values) * 100
        bar = '█' * int(pct / 2)
        print(f"  {rating:.0f} sao: {count:>6,} ({pct:>5.1f}%) {bar}")

# Review count stats
with_reviews = db.bronze_records.count_documents({'review_count': {'$gt': 0}})
print(f"\n📝 POIs có reviews: {with_reviews:,} ({with_reviews/total*100:.1f}%)")

# 5. PHÂN TÍCH GEOGRAPHIC
print("\n\n🗺️ PHÂN TÍCH ĐỊA LÝ")
print("-" * 80)

# North/Central/South distribution
region_map = {
    'hanoi': 'North', 'haiphong': 'North', 'langson': 'North', 
    'thainguyen': 'North', 'vinh': 'North',
    'danang': 'Central', 'hue': 'Central', 'nhatrang': 'Central',
    'quynhon': 'Central', 'tuyhoa': 'Central', 'camranh': 'Central',
    'phanthiet': 'Central', 'dalat': 'Central', 'pleiku': 'Central',
    'hcm': 'South', 'cantho': 'South', 'vungtau': 'South',
    'quangninh': 'North', 'tayninh': 'South', 'longan': 'South'
}

regions = {'North': 0, 'Central': 0, 'South': 0, 'Unknown': 0}
for city_data in cities:
    city = city_data['_id']
    region = region_map.get(city, 'Unknown')
    regions[region] += city_data['count']

print(f"Phân bố theo vùng miền:")
for region, count in regions.items():
    if count > 0:
        pct = count / total * 100
        bar = '█' * int(pct / 2)
        print(f"  {region:>10}: {count:>6,} ({pct:>5.1f}%) {bar}")

# 6. DATA QUALITY ISSUES
print("\n\n⚠️ VẤN ĐỀ DATA QUALITY CẦN XỬ LÝ")
print("-" * 80)

# Missing coordinates
no_coords = db.bronze_records.count_documents({
    '$or': [
        {'location.lat': {'$exists': False}},
        {'location.lng': {'$exists': False}},
        {'location': {'$exists': False}}
    ]
})
print(f"❌ Thiếu tọa độ: {no_coords:,} records")

# Missing names
no_names = db.bronze_records.count_documents({
    '$or': [
        {'name': {'$exists': False}},
        {'name': ''},
        {'name': None}
    ]
})
print(f"❌ Thiếu tên: {no_names:,} records")

# Duplicates check (by poi_id)
pipeline = [
    {'$group': {'_id': '$poi_id', 'count': {'$sum': 1}}},
    {'$match': {'count': {'$gt': 1}}}
]
dups = list(db.bronze_records.aggregate(pipeline))
print(f"⚠️  POI IDs trùng lặp: {len(dups):,} (sẽ được dedupe trong Silver)")

# 7. KHUYẾN NGHỊ CHO SILVER/GOLD
print("\n\n💡 KHUYẾN NGHỊ CHO SILVER → GOLD PROCESSING")
print("-" * 80)

print(f"1. Deduplication:")
print(f"   - Ước tính {len(dups):,} duplicates cần merge")
print(f"   - Criteria: cùng poi_id hoặc tên + tọa độ gần nhau")

print(f"\n2. Normalization:")
print(f"   - {unrated_count:,} POIs cần gán rating mặc định hoặc estimate")
print(f"   - Chuẩn hóa định dạng địa chỉ, tên")
print(f"   - Thêm metadata: region, tier, popularity_score")

print(f"\n3. Enrichment:")
print(f"   - Thêm geohash cho spatial queries")
print(f"   - Tính quality_score dựa trên rating + reviews")
print(f"   - Phân loại POI popularity (high/medium/low)")

print(f"\n4. Validation:")
print(f"   - Loại bỏ {no_coords} POIs thiếu tọa độ")
print(f"   - Loại bỏ {no_names} POIs thiếu tên")
print(f"   - Kiểm tra tọa độ nằm trong bounds Việt Nam")

# 8. DỰ ĐOÁN OUTPUT
print("\n\n📊 DỰ ĐOÁN OUTPUT SAU PROCESSING")
print("-" * 80)

est_valid = total - no_coords - no_names
est_after_dedupe = est_valid * 0.85  # Assume 15% duplicates

print(f"Bronze (input):     {total:,} POIs")
print(f"↓ Filter invalid:   -{no_coords + no_names:,} POIs")
print(f"↓ Deduplicate:      -{est_valid - est_after_dedupe:,.0f} POIs (~15%)")
print(f"Silver (output):    ~{est_after_dedupe:,.0f} POIs")
print(f"↓ Master POI merge: ~10-20% reduction")
print(f"Gold (output):      ~{est_after_dedupe * 0.85:,.0f}-{est_after_dedupe * 0.90:,.0f} POIs")

client.close()

print("\n" + "=" * 80)
print("✅ ANALYSIS COMPLETE")
print("=" * 80)
print(f"\n📌 Sẵn sàng chạy Silver → Gold processing!")
print(f"   Dự kiến: {est_after_dedupe:,.0f} - {est_after_dedupe * 0.90:,.0f} high-quality POIs")
print("=" * 80)
