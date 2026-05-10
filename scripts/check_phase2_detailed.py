#!/usr/bin/env python
"""Detailed Phase 2 check"""
from pymongo import MongoClient

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

print('📊 PHASE 2 DETAILED STATUS')
print('='*60)

# Phase 2 cities
p2_cities = ['vinh', 'quangninh', 'langson', 'thainguyen', 'quynhon',
             'tuyhoa', 'camranh', 'phanthiet', 'vungtau', 'tayninh',
             'longan', 'tiengiang', 'bentre', 'buonmathuot', 'pleiku']

print('📍 Phase 2 Cities:')
total_p2 = 0
for city in p2_cities:
    count = db.bronze_records.count_documents({'city': city})
    if count > 0:
        print(f'  {city}: {count} POIs')
        total_p2 += count

print(f'\n📊 Total Phase 2: {total_p2} POIs')

# Check Phase 2 job details
job = db.collection_jobs.find_one({'phase': 'phase2'}, sort=[('created_at', -1)])
if job:
    print(f'\n💾 Job: {job.get("job_id")}')
    print(f'   Status: {job.get("status")}')
    stats = job.get('stats', {})
    completed = stats.get('completed', 0)
    failed = stats.get('failed', 0)
    total_tasks = completed + failed
    if total_tasks > 0:
        success_rate = completed / total_tasks * 100
        print(f'   Completed: {completed}')
        print(f'   Failed: {failed}')
        print(f'   Success Rate: {success_rate:.1f}%')

client.close()
print('='*60)
