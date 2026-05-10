#!/usr/bin/env python
"""Test POI endpoint directly"""
import requests
import json

# Login
r = requests.post('http://localhost:8000/api/v1/auth/login', 
                  json={'username': 'admin', 'password': 'admin123'})
if r.status_code != 200:
    print(f"Login failed: {r.text}")
    exit(1)

token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Test List POIs
print("Testing GET /api/v1/data/pois?limit=1")
r = requests.get('http://localhost:8000/api/v1/data/pois?limit=1', headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Success! Total: {data.get('total', 0)}")
    if data.get('items'):
        item = data['items'][0]
        print(f"First POI: {item.get('name')} (ID: {item.get('poi_id')})")
else:
    print(f"Error: {r.text[:500]}")

# Test with city
print("\nTesting GET /api/v1/data/pois?city=hanoi&limit=1")
r = requests.get('http://localhost:8000/api/v1/data/pois?city=hanoi&limit=1', headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Success! Total in Hanoi: {data.get('total', 0)}")
else:
    print(f"Error: {r.text[:500]}")

# Test with category
print("\nTesting GET /api/v1/data/pois?category=restaurant&limit=1")
r = requests.get('http://localhost:8000/api/v1/data/pois?category=restaurant&limit=1', headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Success! Total restaurants: {data.get('total', 0)}")
else:
    print(f"Error: {r.text[:500]}")
