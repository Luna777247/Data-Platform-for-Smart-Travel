#!/usr/bin/env python
"""
Process ALL Bronze to Gold
==========================
Xử lý toàn bộ 19,210 bronze records qua Silver → Gold
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from pymongo import MongoClient


class BronzeToGoldProcessor:
    def __init__(self):
        import os
        mongo_uri = os.getenv(
            "MONGODB_URI",
            "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0"
        )
        self.client = MongoClient(mongo_uri)
        self.db = self.client.smart_travel_platform
        
        # Stats
        self.stats = {
            'bronze_total': 0,
            'silver_valid': 0,
            'silver_invalid': 0,
            'gold_master': 0,
            'deduped': 0,
            'by_city': defaultdict(int)
        }
    
    def process_bronze_to_silver(self):
        """Process bronze_pois records to silver_pois."""
        print("=" * 70)
        print("🚀 SILVER PROCESSING - FROM BRONZE_POIS (RAW DATA)")
        print("=" * 70)
        
        # Get all bronze records with osm_raw data from bronze_pois
        bronze_records = list(self.db.bronze_pois.find({
            "has_osm_data": True,
            "osm_raw": {"$exists": True}
        }))
        self.stats['bronze_total'] = len(bronze_records)
        
        print(f"📊 Loaded {len(bronze_records):,} bronze records")
        
        # Deduplicate by poi_id
        seen_poi_ids = set()
        unique_records = []
        duplicates = 0
        
        for record in bronze_records:
            poi_id = record.get('poi_id')
            if poi_id and poi_id in seen_poi_ids:
                duplicates += 1
                continue
            if poi_id:
                seen_poi_ids.add(poi_id)
            unique_records.append(record)
        
        self.stats['deduped'] = duplicates
        print(f"🔍 Found {duplicates:,} duplicates, {len(unique_records):,} unique")
        
        # Process to silver format
        silver_records = []
        for record in unique_records:
            # Skip if missing critical fields
            if not record.get('name') or not record.get('location'):
                self.stats['silver_invalid'] += 1
                continue
            
            # Extract data từ osm_raw.element
            osm_raw = record.get('osm_raw', {})
            element = osm_raw.get('element', {})
            tags = element.get('tags', {})
            
            # Get location from element
            location = record.get('location', {})
            if not location and element:
                if element.get('lat') and element.get('lon'):
                    location = {'lat': element['lat'], 'lon': element['lon']}
                elif element.get('center'):
                    location = {'lat': element['center']['lat'], 'lon': element['center']['lon']}
            
            # Normalize to silver format
            silver_record = {
                'u_key': record.get('u_key'),
                'poi_id': record.get('poi_id'),
                'name': record.get('name', '').strip() or tags.get('name', 'Unknown'),
                'category': record.get('category', 'unknown'),
                'city': record.get('city', 'unknown'),
                'city_name': record.get('city_name'),
                'country': record.get('country', 'Vietnam'),
                'location': location,
                'address': record.get('address') or tags.get('addr:street') or tags.get('addr:full'),
                'phone': record.get('phone') or tags.get('phone'),
                'website': record.get('website') or tags.get('website'),
                'opening_hours': tags.get('opening_hours'),
                'rating': record.get('rating'),
                'review_count': record.get('review_count', 0),
                'google_place_id': record.get('google_place_id'),
                'osm_id': record.get('osm_id'),
                'osm_type': record.get('osm_type'),
                'osm_tags': tags,
                'has_google_data': record.get('has_google_data', False),
                # Lưu reference đến raw data
                '_raw_refs': {
                    'osm_raw_element_id': str(element.get('id')) if element else None,
                    'bronze_pois_u_key': record.get('u_key')
                },
                '_sources': record.get('data_sources', [record.get('_source', 'osm')]),
                '_collected_at': record.get('created_at'),
                '_processed_at': datetime.now().isoformat(),
                '_layer': 'silver'
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(silver_record)
            silver_record['_quality_score'] = quality_score
            
            silver_records.append(silver_record)
            self.stats['silver_valid'] += 1
            self.stats['by_city'][silver_record['city']] += 1
        
        # Clear silver_places and insert
        print(f"💾 Saving {len(silver_records):,} silver records...")
        self.db.silver_places.delete_many({})
        if silver_records:
            self.db.silver_places.insert_many(silver_records, ordered=False)
        
        print(f"✅ Silver: {len(silver_records):,} records saved")
        return silver_records
    
    def _calculate_quality_score(self, record):
        """Calculate quality score 0-100."""
        score = 50  # Base score
        
        # Rating bonus (max 25)
        rating = record.get('rating')
        if rating:
            score += min(rating * 5, 25)
        
        # Review count bonus (max 15)
        reviews = record.get('review_count', 0)
        if reviews > 0:
            score += min(reviews / 10, 15)
        
        # Has address bonus (max 10)
        if record.get('address'):
            score += 10
        
        return min(score, 100)
    
    def process_silver_to_gold(self, silver_records):
        """Process silver to gold master POIs."""
        print("\n" + "=" * 70)
        print("👑 GOLD PROCESSING - MASTER POIs")
        print("=" * 70)
        
        # Enrich and create master POIs
        gold_records = []
        
        for record in silver_records:
            # Add enrichment
            enriched = self._enrich_record(record)
            gold_records.append(enriched)
            self.stats['gold_master'] += 1
        
        # Clear gold_master_pois and insert
        print(f"💾 Saving {len(gold_records):,} gold master POIs...")
        self.db.gold_master_pois.delete_many({})
        if gold_records:
            self.db.gold_master_pois.insert_many(gold_records, ordered=False)
        
        print(f"✅ Gold: {len(gold_records):,} master POIs saved")
        return gold_records
    
    def _enrich_record(self, record):
        """Enrich record with additional metadata."""
        enriched = record.copy()
        
        # Add geohash (simplified - first 6 chars of lat,lng hash)
        location = record.get('location', {})
        lat = location.get('lat', 0)
        lng = location.get('lng', 0)
        
        # Simple geohash approximation
        geohash = f"{int((lat + 90) * 100):04d}{int((lng + 180) * 100):04d}"
        enriched['_geohash'] = geohash[:8]
        
        # Add popularity tier
        quality = record.get('_quality_score', 50)
        reviews = record.get('review_count', 0)
        
        if quality >= 80 and reviews >= 100:
            enriched['_popularity_tier'] = 'high'
        elif quality >= 60 or reviews >= 50:
            enriched['_popularity_tier'] = 'medium'
        else:
            enriched['_popularity_tier'] = 'low'
        
        # Add region
        city = record.get('city', '')
        north_cities = ['hanoi', 'haiphong', 'vinh', 'langson', 'thainguyen', 'quangninh']
        central_cities = ['danang', 'hue', 'nhatrang', 'quynhon', 'tuyhoa', 'camranh', 'phanthiet', 'dalat', 'pleiku']
        
        if city in north_cities:
            enriched['_region'] = 'north'
        elif city in central_cities:
            enriched['_region'] = 'central'
        else:
            enriched['_region'] = 'south'
        
        enriched['_layer'] = 'gold'
        enriched['_enriched_at'] = datetime.now().isoformat()
        
        return enriched
    
    def create_indexes(self):
        """Create indexes for Gold collection."""
        print("\n" + "=" * 70)
        print("🔍 CREATING INDEXES")
        print("=" * 70)
        
        indexes = [
            ('poi_id', True),  # Unique
            ('city', False),
            ('category', False),
            ('_geohash', False),
            ('_popularity_tier', False),
            ('_region', False),
            ('location', '2dsphere'),  # Geospatial
        ]
        
        for field, unique in indexes:
            try:
                if unique == '2dsphere':
                    self.db.gold_master_pois.create_index([(field, '2dsphere')])
                elif unique:
                    self.db.gold_master_pois.create_index(field, unique=True)
                else:
                    self.db.gold_master_pois.create_index(field)
                print(f"  ✅ Index: {field}")
            except Exception as e:
                print(f"  ⚠️  Index {field}: {e}")
        
        print("✅ Indexes created")
    
    def print_summary(self):
        """Print final summary."""
        print("\n" + "=" * 70)
        print("📊 FINAL SUMMARY")
        print("=" * 70)
        
        print(f"\n📈 Processing Results:")
        print(f"  Bronze (input):  {self.stats['bronze_total']:,} records")
        print(f"  ↓ Deduplicate:   -{self.stats['deduped']:,} duplicates")
        print(f"  ↓ Invalid:       -{self.stats['silver_invalid']:,} records")
        print(f"  Silver (output): {self.stats['silver_valid']:,} records")
        print(f"  Gold (output):   {self.stats['gold_master']:,} master POIs")
        
        print(f"\n📍 By City (Top 10):")
        for city, count in sorted(self.stats['by_city'].items(), key=lambda x: -x[1])[:10]:
            print(f"  {city}: {count} POIs")
        
        # Verify counts
        bronze_final = self.db.bronze_records.count_documents({})
        silver_final = self.db.silver_places.count_documents({})
        gold_final = self.db.gold_master_pois.count_documents({})
        
        print(f"\n💾 Database Status:")
        print(f"  Bronze: {bronze_final:,}")
        print(f"  Silver: {silver_final:,}")
        print(f"  Gold:   {gold_final:,}")
        
        print("\n" + "=" * 70)
        print("✅ BRONZE → SILVER → GOLD PROCESSING COMPLETE!")
        print("=" * 70)
    
    def run(self):
        """Run full processing pipeline."""
        try:
            # Step 1: Bronze to Silver
            silver_records = self.process_bronze_to_silver()
            
            # Step 2: Silver to Gold
            gold_records = self.process_silver_to_gold(silver_records)
            
            # Step 3: Create indexes
            self.create_indexes()
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.client.close()


if __name__ == "__main__":
    processor = BronzeToGoldProcessor()
    processor.run()
