#!/usr/bin/env python
"""Test with detail"""
import requests
import traceback

try:
    # Login
    r = requests.post('http://localhost:8000/api/v1/auth/login', 
                      json={'username': 'admin', 'password': 'admin123'},
                      timeout=5)
    print(f'Login: {r.status_code}')
    
    if r.status_code == 200:
        token = r.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test testpublic
        print('\nTesting GET /api/v1/data/testpublic')
        r = requests.get('http://localhost:8000/api/v1/data/testpublic', timeout=5)
        print(f'Status: {r.status_code}')
        print(f'Headers: {dict(r.headers)}')
        print(f'Body: {r.text[:200]}')
        
        # Test testpois
        print('\nTesting GET /api/v1/data/testpois')
        r = requests.get('http://localhost:8000/api/v1/data/testpois', headers=headers, timeout=5)
        print(f'Status: {r.status_code}')
        print(f'Headers: {dict(r.headers)}')
        print(f'Body: {r.text[:200]}')
        
        # Test /pois
        print('\nTesting GET /api/v1/data/pois?limit=1')
        r = requests.get('http://localhost:8000/api/v1/data/pois?limit=1', headers=headers, timeout=5)
        print(f'Status: {r.status_code}')
        print(f'Headers: {dict(r.headers)}')
        print(f'Body: {r.text[:200]}')
        
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()
