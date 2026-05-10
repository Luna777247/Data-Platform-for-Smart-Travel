"""
Gold Processing Script
======================

Chạy Gold layer processing:
- Enrichment
- Aggregation
- Master POI creation
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pymongo import MongoClient
from pipelines.gold.enrichment import GoldEnricher
from pipelines.gold.aggregation import DataAggregator


def run_gold_processing():
    """Run gold processing pipeline."""
    print("🚀 Starting Gold Processing Phase...")
    print("=" * 50)
    
    # Connect to MongoDB
    mongo_uri = "mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin"
    client = MongoClient(mongo_uri)
    db = client.smart_travel
    
    # Initialize processors
    enricher = GoldEnricher()
    aggregator = DataAggregator()
    
    total_enriched = 0
    total_master_pois = 0
    
    # Process each city
    cities = ["hanoi", "hcm", "danang"]
    
    for city in cities:
        print(f"\n📍 Processing city: {city.upper()}")
        
        # Get silver records for this city
        silver_records = list(db.silver_places.find({"city": city, "_source": "mock"}))
        print(f"   📊 Loaded {len(silver_records)} silver records")
        
        if not silver_records:
            print(f"   ⚠️  No silver data for {city}")
            continue
        
        # Step 1: Enrichment
        print("   ✨ Running enrichment...", end=" ")
        try:
            enriched_records = enricher.enrich_batch(silver_records)
            total_enriched += len(enriched_records)
            print(f"✅ {len(enriched_records)} records enriched")
        except Exception as e:
            print(f"❌ Error: {e}")
            enriched_records = silver_records
        
        # Step 2: Prepare master POIs
        print("   👑 Creating master POIs...", end=" ")
        try:
            master_pois = []
            for record in enriched_records:
                master_poi = {
                    "poi_id": record.get("poi_id"),
                    "name": record.get("name"),
                    "name_en": record.get("name_en"),
                    "category": record.get("category"),
                    "city": record.get("city"),
                    "country": record.get("country", "VN"),
                    "location": record.get("location", {}),
                    "address": record.get("address"),
                    "rating": record.get("rating"),
                    "review_count": record.get("review_count", 0),
                    "quality_score": record.get("_validation_score", 0.8) * 100,
                    "popularity_score": record.get("popularity_score", 50),
                    "searchable_text": f"{record.get('name', '')} {record.get('category', '')} {record.get('city', '')}",
                    "keywords": record.get("keywords", []),
                    "sources": ["mock", "silver"],
                    "status": "active",
                    "created_at": record.get("_ingestion_timestamp", datetime.utcnow().isoformat()),
                    "updated_at": datetime.utcnow().isoformat(),
                    "_layer": "gold",
                    "_source": "mock"
                }
                master_pois.append(master_poi)
            
            total_master_pois += len(master_pois)
            print(f"✅ {len(master_pois)} master POIs created")
        except Exception as e:
            print(f"❌ Error: {e}")
            master_pois = []
        
        # Step 3: Save to gold_master_pois
        print("   💾 Saving to gold_master_pois...", end=" ")
        try:
            # Clear existing gold data for this city
            db.gold_master_pois.delete_many({"city": city, "_source": "mock"})
            
            if master_pois:
                result = db.gold_master_pois.insert_many(master_pois)
                inserted = len(result.inserted_ids)
                print(f"✅ {inserted} records saved")
            else:
                print(f"⚠️  No records to save")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📈 GOLD PROCESSING COMPLETE")
    print(f"   Total enriched records: {total_enriched}")
    print(f"   Total master POIs: {total_master_pois}")
    
    # Verify
    gold_count = db.gold_master_pois.count_documents({"_source": "mock"})
    print(f"   Gold collection size: {gold_count}")
    
    # Show breakdown
    for city in cities:
        city_count = db.gold_master_pois.count_documents({"city": city, "_source": "mock"})
        print(f"   - {city}: {city_count} records")
    
    client.close()
    print("\n✅ Gold processing finished!")


if __name__ == "__main__":
    run_gold_processing()
