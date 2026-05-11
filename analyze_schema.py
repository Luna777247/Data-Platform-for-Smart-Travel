#!/usr/bin/env python3
"""So sánh chi tiết schema: Storage vs MongoDB"""
import sys
sys.path.insert(0, '.')

import json
import os
from collections import defaultdict
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings
import asyncio


def analyze_json_structure(data, prefix="", max_depth=3, current_depth=0):
    """Trích xuất cấu trúc từ JSON"""
    if current_depth >= max_depth:
        return {"...": "max_depth"}
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result[key] = analyze_json_structure(value, f"{prefix}.{key}", max_depth, current_depth + 1)
        return result
    elif isinstance(data, list) and data:
        return [analyze_json_structure(data[0], prefix, max_depth, current_depth + 1)]
    else:
        return type(data).__name__


def get_sample_from_storage(path, num_samples=5):
    """Lấy mẫu từ storage"""
    samples = []
    count = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith('.json') and count < num_samples:
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, encoding='utf-8') as fp:
                        data = json.load(fp)
                        samples.append({
                            'file': filepath.replace(path, ''),
                            'data': data
                        })
                        count += 1
                except:
                    pass
    return samples


async def analyze_mongodb_schema(db, collection_name, sample_size=5):
    """Phân tích schema MongoDB"""
    samples = []
    async for doc in db[collection_name].find().limit(sample_size):
        # Convert ObjectId to string for JSON serialization
        doc['_id'] = str(doc['_id'])
        samples.append(doc)
    
    # Get all unique keys
    all_keys = set()
    async for doc in db[collection_name].find():
        all_keys.update(doc.keys())
    
    return {
        'samples': samples,
        'all_keys': sorted(all_keys),
        'count': await db[collection_name].count_documents({})
    }


async def compare():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_database]
    
    print("=" * 70)
    print("SO SÁNH CHI TIẾT: STORAGE vs MONGODB")
    print("=" * 70)
    
    # =================== MONGODB ANALYSIS ===================
    print("\n" + "=" * 70)
    print("📊 MONGODB COLLECTIONS")
    print("=" * 70)
    
    collections = ['places', 'place_metadata', 'tours', 'users', 'tour_users', 
                   'bronze_osm_raw', 'bronze_google_raw', 'silver_pois', 'gold_master_pois']
    
    for coll in collections:
        count = await db[coll].count_documents({})
        if count > 0:
            print(f"\n🔹 {coll}: {count:,} documents")
            analysis = await analyze_mongodb_schema(db, coll, 3)
            print(f"   Fields: {', '.join(analysis['all_keys'][:15])}{'...' if len(analysis['all_keys']) > 15 else ''}")
            
            if analysis['samples']:
                sample = analysis['samples'][0]
                structure = analyze_json_structure(sample, max_depth=2)
                print(f"   Sample keys: {list(structure.keys())[:10]}")
    
    # =================== STORAGE ANALYSIS ===================
    print("\n" + "=" * 70)
    print("📁 STORAGE FILES")
    print("=" * 70)
    
    # Bronze layer
    print("\n🥉 BRONZE LAYER (Raw Data)")
    bronze_samples = get_sample_from_storage('storage/bronze', 3)
    
    for i, sample in enumerate(bronze_samples[:2], 1):
        print(f"\n   Sample {i}: {sample['file']}")
        data = sample['data']
        if isinstance(data, dict):
            print(f"   ├── Root type: dict")
            print(f"   ├── Keys: {list(data.keys())[:15]}")
            if len(data.keys()) > 15:
                print(f"   └── ... và {len(data.keys()) - 15} keys khác")
            
            # Check nested structures
            for key in list(data.keys())[:5]:
                value = data[key]
                if isinstance(value, dict):
                    print(f"   ├── {key}: dict với {len(value)} keys")
                elif isinstance(value, list):
                    print(f"   ├── {key}: list[{len(value)} items]")
                else:
                    print(f"   ├── {key}: {type(value).__name__} = {str(value)[:50]}")
    
    # File counts by source
    print("\n   📊 Thống kê theo nguồn:")
    sources = defaultdict(int)
    for root, dirs, files in os.walk('storage/bronze'):
        for f in files:
            if f.endswith('.json'):
                # Extract source from path
                parts = root.replace('storage/bronze/', '').split('/')
                if parts:
                    source = parts[0] if parts[0] else 'unknown'
                    sources[source] += 1
    
    for source, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"      • {source}: {count:,} files")
    
    # =================== COMPARISON ===================
    print("\n" + "=" * 70)
    print("🔍 SO SÁNH CHI TIẾT")
    print("=" * 70)
    
    # Compare bronze storage vs bronze_mongodb
    bronze_count = sum(sources.values())
    mongo_bronze = await db['bronze_osm_raw'].count_documents({})
    mongo_bronze += await db['bronze_google_raw'].count_documents({})
    
    print(f"\n🥉 Bronze Layer:")
    print(f"   • Storage: {bronze_count:,} files (raw JSON)")
    print(f"   • MongoDB: {mongo_bronze:,} documents")
    print(f"   • Chênh lệch: {bronze_count - mongo_bronze:,} files chưa import")
    
    # Gold layer comparison
    mongo_gold = await db['gold_master_pois'].count_documents({})
    silver_count = sum(1 for root, dirs, files in os.walk('storage/silver') 
                       for f in files if f.endswith('.json'))
    gold_count = sum(1 for root, dirs, files in os.walk('storage/gold') 
                     for f in files if f.endswith('.json'))
    
    print(f"\n🥈 Silver Layer:")
    print(f"   • Storage: {silver_count} files")
    print(f"   • MongoDB: {await db['silver_pois'].count_documents({})} documents")
    
    print(f"\n🥇 Gold Layer:")
    print(f"   • Storage: {gold_count} files")
    print(f"   • MongoDB: {mongo_gold} documents")
    
    # =================== FIELD MAPPING ===================
    print("\n" + "=" * 70)
    print("📋 FIELD MAPPING (Storage → MongoDB)")
    print("=" * 70)
    
    if bronze_samples:
        sample = bronze_samples[0]['data']
        if isinstance(sample, dict):
            print("\n   Storage fields (Google Places API format):")
            google_fields = list(sample.keys())
            for field in google_fields[:20]:
                mapped = ""
                if 'place_id' in field.lower():
                    mapped = " → places.place_id"
                elif 'name' in field.lower():
                    mapped = " → places.name"
                elif 'location' in field.lower() or 'geometry' in field.lower():
                    mapped = " → places.location"
                elif 'types' in field.lower() or 'category' in field.lower():
                    mapped = " → places.category"
                elif 'rating' in field.lower():
                    mapped = " → places.rating"
                elif 'formatted_address' in field.lower() or 'vicinity' in field.lower():
                    mapped = " → places.address"
                print(f"      • {field}{mapped}")
    
    # Check places collection schema
    places_analysis = await analyze_mongodb_schema(db, 'places', 1)
    if places_analysis['samples']:
        print(f"\n   MongoDB 'places' fields:")
        for field in places_analysis['all_keys'][:20]:
            print(f"      • {field}")
    
    print("\n" + "=" * 70)
    print("💡 KẾT LUẬN")
    print("=" * 70)
    
    if bronze_count > mongo_bronze * 2:
        print("\n   ⚠️  Storage có nhiều dữ liệu RAW chưa được xử lý:")
        print(f"      • {bronze_count:,} files trong storage")
        print(f"      • Chỉ {mongo_bronze:,} documents trong MongoDB bronze")
        print("\n   → Cần chạy pipeline để:")
        print("      1. Import từ storage → MongoDB bronze")
        print("      2. Transform bronze → silver (cleaning)")
        print("      3. Enrich silver → gold (master data)")
    
    client.close()


if __name__ == '__main__':
    asyncio.run(compare())
