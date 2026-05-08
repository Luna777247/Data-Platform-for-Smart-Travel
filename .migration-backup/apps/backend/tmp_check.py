import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from app.db.client import MongoClient
from app.db.repository import PlaceRepository

async def check_data():
    await MongoClient.connect()
    repo = PlaceRepository()
    all_places = await repo.get_all(limit=1000)
    
    cities = set()
    types = set()
    
    for p in all_places:
        cities.add(str(p.get("city")))
        types.add(str(p.get("type")))
    
    print("Cities found:", cities)
    print("Types found:", types)
    
    if all_places:
        print("Sample types:", {p.get("type") for p in all_places[:20]})

if __name__ == "__main__":
    asyncio.run(check_data())
