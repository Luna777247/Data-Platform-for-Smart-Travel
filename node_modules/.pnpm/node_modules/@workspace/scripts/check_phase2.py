#!/usr/bin/env python
"""Check Phase 2 collection status"""
from pymongo import MongoClient

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

job = db.collection_jobs.find_one({'phase': 'phase2'}, sort=[('created_at', -1)])
if job:
    print(f'Phase 2 Job: {job.get("job_id")}')
    print(f'Status: {job.get("status")}')
    stats = job.get('stats', {})
    print(f'Completed: {stats.get("completed", 0)}')
    print(f'Failed: {stats.get("failed", 0)}')
    print(f'New POIs: {stats.get("total_records", 0)}')
else:
    print('Phase 2 job not completed yet')

p2_count = db.bronze_records.count_documents({'_job_id': {'$regex': 'mass_p2_'}})
print(f'Total Phase 2 POIs: {p2_count}')

total = db.bronze_records.count_documents({})
print(f'Total Bronze: {total}')

client.close()
