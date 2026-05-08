
import asyncio
import sys
import os

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "apps", "backend"))

from app.db.client import MongoClient

async def check_beijing():
    await MongoClient.connect()
    db = MongoClient.db
    count = await db.places.count_documents({"city": "beijing"})
    print(f"Beijing POIs count: {count}")
    
    # Check for specific famous place
    museum = await db.places.find_one({"name": {"$regex": "Palace Museum", "$options": "i"}})
    if museum:
        print(f"Found Museum: {museum['name']} with rating {museum.get('rating')}")
        
    await MongoClient.disconnect()

if __name__ == "__main__":
    asyncio.run(check_beijing())
