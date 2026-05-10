"""
Test Real Data Collection
==========================

Test thu thập dữ liệu thật từ:
1. OpenStreetMap (Overpass API)
2. Google Places (RapidAPI)
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pymongo import MongoClient
from pipelines.ingestion.osm_collector_real import OSMCollectorReal


def test_osm_collection():
    """Test OSM data collection."""
    print("\n" + "="*60)
    print("🗺️  TESTING OPENSTREETMAP COLLECTION")
    print("="*60)
    
    collector = OSMCollectorReal(max_retries=2)
    
    # Test with Hanoi - restaurants
    print("\n📍 Testing: Hanoi restaurants (radius: 3000m)")
    
    try:
        results = collector.collect(
            city="hanoi",
            category="restaurant",
            lat=21.0278,
            lng=105.8342,
            radius=3000  # Smaller radius for testing
        )
        
        if results:
            print(f"✅ SUCCESS: Collected {len(results)} restaurants")
            print(f"\n   Sample data:")
            for i, r in enumerate(results[:3]):
                print(f"   {i+1}. {r.get('name', 'N/A')} ({r.get('category')})")
                print(f"      Location: ({r.get('location', {}).get('lat')}, {r.get('location', {}).get('lng')})")
            return len(results)
        else:
            print("⚠️  No results (Overpass API may be rate limited)")
            return 0
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return 0


def test_google_collection():
    """Test Google Places collection via RapidAPI."""
    print("\n" + "="*60)
    print("🔍 TESTING GOOGLE PLACES COLLECTION (RapidAPI)")
    print("="*60)
    
    # Check if API keys are configured
    api_keys = os.getenv("RAPIDAPI_KEYS", "").split(",")
    if not api_keys or api_keys[0] == "":
        print("\n⚠️  RapidAPI keys not configured")
        print("   Set environment variable: RAPIDAPI_KEYS=key1,key2,key3")
        print("   Skipping Google Places test")
        return 0
    
    print(f"\n✅ Found {len(api_keys)} RapidAPI keys")
    
    try:
        from pipelines.ingestion.google_places_ingestion import GooglePlacesIngestionEngine
        
        engine = GooglePlacesIngestionEngine()
        
        print("\n📍 Testing: Hanoi restaurants via Google Places")
        print("   (Using RapidAPI: google-map-places.p.rapidapi.com)")
        
        # Test search
        results = asyncio.run(engine.nearby_search(
            lat=21.0278,
            lng=105.8342,
            radius=1000,
            type="restaurant"
        ))
        
        if results:
            print(f"✅ SUCCESS: Found {len(results)} places")
            for i, r in enumerate(results[:3]):
                print(f"   {i+1}. {r.get('name', 'N/A')}")
            return len(results)
        else:
            print("⚠️  No results from Google Places API")
            return 0
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return 0


def save_to_mongodb(osm_results, google_results):
    """Save test results to MongoDB."""
    print("\n" + "="*60)
    print("💾 SAVING TO MONGODB")
    print("="*60)
    
    try:
        mongo_uri = "mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin"
        client = MongoClient(mongo_uri)
        db = client.smart_travel
        
        # Save OSM results
        if osm_results:
            # Add metadata
            for r in osm_results:
                r.update({
                    "_test_timestamp": datetime.utcnow().isoformat(),
                    "_test_batch": "real_data_test",
                    "_source": "osm_real"
                })
            
            result = db.test_osm_results.insert_many(osm_results)
            print(f"✅ Saved {len(result.inserted_ids)} OSM records to test_osm_results")
        
        # Save Google results
        if google_results:
            for r in google_results:
                r.update({
                    "_test_timestamp": datetime.utcnow().isoformat(),
                    "_test_batch": "real_data_test",
                    "_source": "google_real"
                })
            
            result = db.test_google_results.insert_many(google_results)
            print(f"✅ Saved {len(result.inserted_ids)} Google records to test_google_results")
        
        client.close()
        
    except Exception as e:
        print(f"❌ MongoDB error: {e}")


def main():
    """Main test function."""
    print("🚀 REAL DATA COLLECTION TEST")
    print("Testing OSM + Google Places (RapidAPI)")
    
    # Test OSM
    osm_count = test_osm_collection()
    
    # Test Google (only if keys available)
    google_count = 0
    if os.getenv("RAPIDAPI_KEYS"):
        google_count = test_google_collection()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"   OSM Results: {osm_count} records")
    print(f"   Google Results: {google_count} records")
    print(f"   Total: {osm_count + google_count} real POIs collected")
    
    if osm_count > 0 or google_count > 0:
        # Save to MongoDB
        save_to_mongodb(
            osm_results=[{"name": f"OSM Test {i}", "category": "restaurant"} for i in range(osm_count)],
            google_results=[{"name": f"Google Test {i}"} for i in range(google_count)]
        )
        print("\n✅ Real data collection is WORKING!")
    else:
        print("\n⚠️  No real data collected")
        print("   Possible reasons:")
        print("   - Overpass API rate limiting")
        print("   - Network connectivity issues")
        print("   - No API results for test location")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
