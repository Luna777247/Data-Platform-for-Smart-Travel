"""
Insert Test Data into MongoDB
=============================

Script để insert 60 test POI records vào MongoDB.
20 records per city: hanoi, hcm, danang
"""

import asyncio
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

# Test data configuration
CITIES = {
    "hanoi": {"lat": 21.0278, "lng": 105.8342, "country": "VN"},
    "hcm": {"lat": 10.8231, "lng": 106.6297, "country": "VN"},
    "danang": {"lat": 16.0544, "lng": 108.2022, "country": "VN"}
}

CATEGORIES = ["restaurant", "hotel", "tourist_attraction", "cafe", "shopping_mall", "park", "museum"]

POI_NAMES = {
    "restaurant": ["Pho 24", "Highlands Coffee", "The Pizza Company", "KFC", "Pizza Hut", "Bun Cha Hang Manh", "Com Tam Cali", "Lotteria", "Jollibee", "BBQ Chicken"],
    "hotel": ["Sofitel Legend Metropole", "JW Marriott", "InterContinental", "Pullman", "Novotel", "Hilton", "Hyatt", "Sheraton", "Melia", "Majestic"],
    "tourist_attraction": ["Hoan Kiem Lake", "Ben Thanh Market", "Dragon Bridge", "Old Quarter", "War Remnants Museum", "Marble Mountains", "Temple of Literature", "Cu Chi Tunnels", "My Khe Beach", "Ho Chi Minh Mausoleum"],
    "cafe": ["Cong Caphe", "The Coffee House", "Starbucks", "Trung Nguyen", "Cafe Giang", "Cafe Dinh", "Runam Bistro", "LUsine", "Shin Coffee", "Workshop Coffee"],
    "shopping_mall": ["Vincom Center", "AEON Mall", "Lotte Mart", "Big C", "Co.opmart", "Saigon Centre", "Indochina Plaza", "Times City", "Royal City", "Crescent Mall"],
    "park": ["Tao Dan Park", "Thong Nhat Park", "Yen So Park", "Thu Le Zoo", "Gia Dinh Park", "23/9 Park", "Ho Tay Park", "Le Van Tam Park", "30/4 Park", "September 23 Park"],
    "museum": ["Vietnam Museum of Ethnology", "Fine Arts Museum", "History Museum", "Ho Chi Minh Museum", "War Remnants Museum", "Cham Museum", "Ao Dai Museum", "Revolutionary Museum", "Air Force Museum", "Police Museum"]
}


def generate_poi(poi_id: int, city: str, category: str) -> dict:
    """Generate a single POI document."""
    city_info = CITIES[city]
    base_lat = city_info["lat"]
    base_lng = city_info["lng"]
    
    # Random offset within ~5km
    lat_offset = random.uniform(-0.05, 0.05)
    lng_offset = random.uniform(-0.05, 0.05)
    
    name = random.choice(POI_NAMES[category])
    unique_name = f"{name} {poi_id}"
    
    # Generate random rating between 3.5 and 5.0
    rating = round(random.uniform(3.5, 5.0), 1)
    review_count = random.randint(10, 5000)
    
    # Generate address
    street_numbers = ["123", "45", "789", "12A", "88", "256", "42", "99", "1", "168"]
    streets = ["Le Loi", "Nguyen Hue", "Tran Hung Dao", "Dien Bien Phu", "Hai Ba Trung", "Pasteur", "Ly Tu Trong", "Ham Nghi", "Ton Duc Thang", "Vo Van Tan"]
    
    address = f"{random.choice(street_numbers)} {random.choice(streets)}, {city.title()}"
    
    return {
        "_id": f"poi_{city}_{category}_{poi_id}",
        "name": unique_name,
        "category": category,
        "city": city,
        "country": city_info["country"],
        "location": {
            "lat": round(base_lat + lat_offset, 6),
            "lng": round(base_lng + lng_offset, 6)
        },
        "address": address,
        "rating": rating,
        "user_ratings_total": review_count,
        "quality_score": round(random.uniform(60, 98), 1),
        "status": "active",
        "sources": ["manual", "test_data"],
        "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 365)),
        "updated_at": datetime.utcnow(),
        "layer": "gold",
        "phone": f"+84 {random.randint(20, 99)} {random.randint(100, 999)} {random.randint(100, 999)}",
        "website": f"https://example.com/{unique_name.lower().replace(' ', '-')}",
        "opening_hours": {
            "monday": "08:00-22:00",
            "tuesday": "08:00-22:00",
            "wednesday": "08:00-22:00",
            "thursday": "08:00-22:00",
            "friday": "08:00-23:00",
            "saturday": "08:00-23:00",
            "sunday": "08:00-22:00"
        },
        "tags": [category, city, "test"]
    }


async def insert_test_data():
    """Insert test data into MongoDB."""
    # Connect to MongoDB with authentication
    import os
    mongo_host = os.getenv("MONGO_HOST", "localhost")
    mongo_port = os.getenv("MONGO_PORT", "27017")
    mongo_user = os.getenv("MONGO_USER", "admin")
    mongo_pass = os.getenv("MONGO_PASSWORD", "secret_password")
    
    # Build connection string with auth
    if mongo_user and mongo_pass:
        uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}"
    else:
        uri = f"mongodb://{mongo_host}:{mongo_port}"
    
    client = AsyncIOMotorClient(uri)
    db = client.smart_travel
    
    print("🗑️  Cleaning existing test data...")
    await db.gold_master_pois.delete_many({"sources": "test_data"})
    
    print("📊 Generating test data...")
    pois = []
    poi_id = 1
    
    for city in CITIES.keys():
        for _ in range(20):  # 20 POIs per city
            category = random.choice(CATEGORIES)
            poi = generate_poi(poi_id, city, category)
            pois.append(poi)
            poi_id += 1
    
    print(f"💾 Inserting {len(pois)} POIs into gold_master_pois...")
    
    if pois:
        result = await db.gold_master_pois.insert_many(pois)
        print(f"✅ Inserted {len(result.inserted_ids)} documents")
    
    # Verify insertion
    count = await db.gold_master_pois.count_documents({"sources": "test_data"})
    print(f"📈 Total test POIs in database: {count}")
    
    # Show sample by city
    for city in CITIES.keys():
        city_count = await db.gold_master_pois.count_documents({"city": city, "sources": "test_data"})
        print(f"   - {city}: {city_count} POIs")
    
    client.close()
    print("\n🎉 Test data insertion complete!")


if __name__ == "__main__":
    asyncio.run(insert_test_data())
