import unittest
import asyncio
import os
import sys
from datetime import datetime, timedelta

# Path config
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)
sys.path.append(os.path.join(root, "apps", "backend"))

from app.utils.auth import create_access_token
from app.db.repository import PlaceRepository
from app.db.client import MongoClient

class TestEnterpriseFeatures(unittest.TestCase):
    async def run_security_tests(self):
        await MongoClient.connect()
        repo = PlaceRepository()
        
        # 1. JWT Generation
        token = create_access_token({"sub": "admin@smart.io", "role": "Administrator"})
        self.assertIsNotNone(token)
        
        # 2. RBAC check (via DB)
        roles = await repo.get_roles()
        self.assertTrue(any(r["name"] == "Administrator" for r in roles))
        
        # 3. Data Quality Logging
        # SilverProcessor ghi log vào collection: data_quality_stats
        logs = await repo.db["data_quality_stats"].find().to_list(10)
        self.assertIsInstance(logs, list)
        
        await MongoClient.disconnect()

    def test_enterprise_security(self):
        asyncio.run(self.run_security_tests())

if __name__ == "__main__":
    unittest.main()
