#!/usr/bin/env python
"""Test simple endpoint to verify code is loaded"""
import requests

# Test health endpoint
r = requests.get('http://localhost:8000/health')
print(f"Health: {r.status_code}")

# Test cities endpoint (working)
r = requests.get('http://localhost:8000/api/v1/data/cities', 
                 headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc2NzIxNjAwMH0.test'})
print(f"Cities: {r.status_code}")
if r.status_code == 200:
    print(f"Cities count: {len(r.json())}")

# Test list POIs
r = requests.get('http://localhost:8000/api/v1/data/pois?limit=1',
                 headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc2NzIxNjAwMH0.test'})
print(f"List POIs: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Total: {data.get('total')}")
    if data.get('items'):
        first = data['items'][0]
        print(f"First item keys: {list(first.keys())[:5]}")
else:
    print(f"Error: {r.text[:200]}")
