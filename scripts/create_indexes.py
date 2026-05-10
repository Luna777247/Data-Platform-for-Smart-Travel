"""
Create MongoDB Indexes
======================

Tạo indexes cho các collections:
- Text index cho search
- Geospatial index cho location queries
- Regular indexes cho filtering
"""

from pymongo import MongoClient, TEXT, ASCENDING, DESCENDING
from pymongo.operations import IndexModel


def create_indexes():
    """Create all required indexes."""
    print("🚀 Creating MongoDB Indexes...")
    print("=" * 50)
    
    # Connect to MongoDB
    mongo_uri = "mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin"
    client = MongoClient(mongo_uri)
    db = client.smart_travel
    
    # 1. Gold Master POIs Indexes
    print("\n📍 Creating indexes for gold_master_pois...")
    
    try:
        # Text index for search
        db.gold_master_pois.create_index(
            [("name", TEXT), ("searchable_text", TEXT)],
            name="text_search_idx",
            background=True
        )
        print("   ✅ Text index created")
    except Exception as e:
        print(f"   ⚠️  Text index: {e}")
    
    try:
        # Regular indexes
        db.gold_master_pois.create_index([("city", ASCENDING)], background=True)
        db.gold_master_pois.create_index([("category", ASCENDING)], background=True)
        db.gold_master_pois.create_index([("quality_score", DESCENDING)], background=True)
        db.gold_master_pois.create_index([("rating", DESCENDING)], background=True)
        print("   ✅ Regular indexes created")
    except Exception as e:
        print(f"   ⚠️  Regular indexes: {e}")
    
    # 2. Silver Places Indexes
    print("\n📍 Creating indexes for silver_places...")
    
    try:
        db.silver_places.create_index([("city", ASCENDING)], background=True)
        db.silver_places.create_index([("category", ASCENDING)], background=True)
        db.silver_places.create_index([("poi_id", ASCENDING)], background=True)
        print("   ✅ Indexes created")
    except Exception as e:
        print(f"   ⚠️  Silver indexes: {e}")
    
    # 3. Bronze Records Indexes
    print("\n📍 Creating indexes for bronze_records...")
    
    try:
        db.bronze_records.create_index([("_city", ASCENDING)], background=True)
        db.bronze_records.create_index([("_category", ASCENDING)], background=True)
        db.bronze_records.create_index([("_source", ASCENDING)], background=True)
        print("   ✅ Indexes created")
    except Exception as e:
        print(f"   ⚠️  Bronze indexes: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📈 INDEX CREATION COMPLETE")
    
    # List all indexes
    print("\n📊 Current Indexes:")
    
    for coll_name in ["gold_master_pois", "silver_places", "bronze_records"]:
        try:
            coll = db[coll_name]
            indexes = list(coll.list_indexes())
            print(f"\n   {coll_name}:")
            for idx in indexes:
                print(f"     - {idx['name']}: {idx['key']}")
        except Exception as e:
            print(f"   {coll_name}: Error - {e}")
    
    client.close()
    print("\n✅ Index creation finished!")


if __name__ == "__main__":
    create_indexes()
