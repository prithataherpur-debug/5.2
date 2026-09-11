#!/usr/bin/env python3
"""
Debug script to see actual my-report response structure
"""

import requests
import json

BASE_URL = "https://open-access-100.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

ADMIN_CREDS = {"username": "admin", "password": "Admin@2026"}
EMP_CREDS = {"username": "emp1", "password": "Emp@2026"}

def login(creds):
    resp = requests.post(f"{API_BASE}/auth/login", json=creds, timeout=10)
    return resp.json()["access_token"]

# Test with admin
admin_token = login(ADMIN_CREDS)
resp = requests.get(f"{API_BASE}/stats/my-report?weeks=2&months=2", 
                   headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)

print("="*80)
print("ADMIN RESPONSE:")
print("="*80)
data = resp.json()
print(f"Top-level keys: {list(data.keys())}")
print(f"is_admin: {data.get('is_admin')}")
print(f"\nWeekly buckets count: {len(data.get('weekly', []))}")
if data.get('weekly'):
    print(f"First weekly bucket keys: {list(data['weekly'][0].keys())}")
    print(f"First weekly bucket: {json.dumps(data['weekly'][0], indent=2)}")

print(f"\nMonthly buckets count: {len(data.get('monthly', []))}")
if data.get('monthly'):
    print(f"First monthly bucket keys: {list(data['monthly'][0].keys())}")
    print(f"First monthly bucket: {json.dumps(data['monthly'][0], indent=2)}")

# Test with employee
print("\n" + "="*80)
print("EMPLOYEE RESPONSE:")
print("="*80)
emp_token = login(EMP_CREDS)
resp = requests.get(f"{API_BASE}/stats/my-report?weeks=2&months=2", 
                   headers={"Authorization": f"Bearer {emp_token}"}, timeout=10)

data = resp.json()
print(f"Top-level keys: {list(data.keys())}")
print(f"is_admin: {data.get('is_admin')}")
print(f"\nWeekly buckets count: {len(data.get('weekly', []))}")
if data.get('weekly'):
    print(f"First weekly bucket keys: {list(data['weekly'][0].keys())}")
    print(f"First weekly bucket: {json.dumps(data['weekly'][0], indent=2)}")

print(f"\nMonthly buckets count: {len(data.get('monthly', []))}")
if data.get('monthly'):
    print(f"First monthly bucket keys: {list(data['monthly'][0].keys())}")
    print(f"First monthly bucket: {json.dumps(data['monthly'][0], indent=2)}")
