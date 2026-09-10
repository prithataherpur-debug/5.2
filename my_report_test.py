#!/usr/bin/env python3
"""
Backend API test for my-report endpoint with invoices and profit
Tests GET /api/stats/my-report with admin and employee users
"""

import requests
import json
from typing import Optional, Dict

# Configuration
BASE_URL = "https://credit-persistence.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials
ADMIN_CREDS = {"username": "admin", "password": "Admin@2026"}
EMP_CREDS = {"username": "emp1", "password": "Emp@2026"}


def log_test(name: str, status: str, details: str = ""):
    """Log test result"""
    symbol = "✅" if status == "PASS" else "❌"
    print(f"\n{symbol} {name}: {status}")
    if details:
        print(f"   {details}")


def login(creds: Dict[str, str]) -> str:
    """Login and return access token"""
    resp = requests.post(f"{API_BASE}/auth/login", json=creds, timeout=10)
    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.status_code} {resp.text}")
    data = resp.json()
    return data["access_token"]


def auth_headers(token: str) -> Dict[str, str]:
    """Return authorization headers"""
    return {"Authorization": f"Bearer {token}"}


def test_my_report_admin():
    """Test GET /api/stats/my-report with admin user"""
    print("\n" + "="*80)
    print("TEST 1: GET /api/stats/my-report with ADMIN user")
    print("="*80)
    
    admin_token = login(ADMIN_CREDS)
    resp = requests.get(f"{API_BASE}/stats/my-report?weeks=8&months=6", 
                       headers=auth_headers(admin_token), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test 1 (Admin my-report)", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return
    
    data = resp.json()
    
    # Verify is_admin flag
    if not data.get("is_admin"):
        log_test("Test 1 (Admin my-report)", "FAIL", f"Expected is_admin=true for admin user, got {data.get('is_admin')}")
        return
    
    # Verify weekly and monthly buckets exist
    if "weekly" not in data or "monthly" not in data:
        log_test("Test 1 (Admin my-report)", "FAIL", f"Missing weekly or monthly buckets. Keys: {data.keys()}")
        return
    
    weekly = data.get("weekly", [])
    monthly = data.get("monthly", [])
    
    if len(weekly) != 8:
        log_test("Test 1 (Admin my-report)", "FAIL", f"Expected 8 weekly buckets, got {len(weekly)}")
        return
    
    if len(monthly) != 6:
        log_test("Test 1 (Admin my-report)", "FAIL", f"Expected 6 monthly buckets, got {len(monthly)}")
        return
    
    # Check first bucket structure (should have all required fields)
    if weekly:
        bucket = weekly[0]
        required_fields = ["start", "end", "calls", "breakdown", "sales_count", "revenue"]
        missing_fields = [f for f in required_fields if f not in bucket]
        if missing_fields:
            log_test("Test 1 (Admin my-report)", "FAIL", f"Weekly bucket missing fields: {missing_fields}")
            return
        
        # Admin should see invoices_count and profit
        if "invoices_count" not in bucket:
            log_test("Test 1 (Admin my-report)", "FAIL", "Weekly bucket missing 'invoices_count' field")
            return
        
        if "profit" not in bucket:
            log_test("Test 1 (Admin my-report)", "FAIL", "Admin user should see 'profit' field in weekly bucket")
            return
    
    if monthly:
        bucket = monthly[0]
        required_fields = ["key", "calls", "breakdown", "sales_count", "revenue"]
        missing_fields = [f for f in required_fields if f not in bucket]
        if missing_fields:
            log_test("Test 1 (Admin my-report)", "FAIL", f"Monthly bucket missing fields: {missing_fields}")
            return
        
        # Admin should see invoices_count and profit
        if "invoices_count" not in bucket:
            log_test("Test 1 (Admin my-report)", "FAIL", "Monthly bucket missing 'invoices_count' field")
            return
        
        if "profit" not in bucket:
            log_test("Test 1 (Admin my-report)", "FAIL", "Admin user should see 'profit' field in monthly bucket")
            return
    
    log_test("Test 1 (Admin my-report)", "PASS", 
             f"Admin sees is_admin=true, 8 weekly + 6 monthly buckets with invoices_count and profit fields")


def test_my_report_employee():
    """Test GET /api/stats/my-report with employee user"""
    print("\n" + "="*80)
    print("TEST 2: GET /api/stats/my-report with EMPLOYEE user")
    print("="*80)
    
    emp_token = login(EMP_CREDS)
    resp = requests.get(f"{API_BASE}/stats/my-report?weeks=8&months=6", 
                       headers=auth_headers(emp_token), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test 2 (Employee my-report)", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return
    
    data = resp.json()
    
    # Verify is_admin flag is false
    if data.get("is_admin") != False:
        log_test("Test 2 (Employee my-report)", "FAIL", f"Expected is_admin=false for employee user, got {data.get('is_admin')}")
        return
    
    # Verify weekly and monthly buckets exist
    if "weekly" not in data or "monthly" not in data:
        log_test("Test 2 (Employee my-report)", "FAIL", f"Missing weekly or monthly buckets. Keys: {data.keys()}")
        return
    
    weekly = data.get("weekly", [])
    monthly = data.get("monthly", [])
    
    if len(weekly) != 8:
        log_test("Test 2 (Employee my-report)", "FAIL", f"Expected 8 weekly buckets, got {len(weekly)}")
        return
    
    if len(monthly) != 6:
        log_test("Test 2 (Employee my-report)", "FAIL", f"Expected 6 monthly buckets, got {len(monthly)}")
        return
    
    # Check first bucket structure
    if weekly:
        bucket = weekly[0]
        required_fields = ["start", "end", "calls", "breakdown", "sales_count", "revenue"]
        missing_fields = [f for f in required_fields if f not in bucket]
        if missing_fields:
            log_test("Test 2 (Employee my-report)", "FAIL", f"Weekly bucket missing fields: {missing_fields}")
            return
        
        # Employee should see invoices_count but NOT profit
        if "invoices_count" not in bucket:
            log_test("Test 2 (Employee my-report)", "FAIL", "Weekly bucket missing 'invoices_count' field")
            return
        
        if "profit" in bucket:
            log_test("Test 2 (Employee my-report)", "FAIL", "Employee user should NOT see 'profit' field in weekly bucket (admin-only)")
            return
    
    if monthly:
        bucket = monthly[0]
        required_fields = ["key", "calls", "breakdown", "sales_count", "revenue"]
        missing_fields = [f for f in required_fields if f not in bucket]
        if missing_fields:
            log_test("Test 2 (Employee my-report)", "FAIL", f"Monthly bucket missing fields: {missing_fields}")
            return
        
        # Employee should see invoices_count but NOT profit
        if "invoices_count" not in bucket:
            log_test("Test 2 (Employee my-report)", "FAIL", "Monthly bucket missing 'invoices_count' field")
            return
        
        if "profit" in bucket:
            log_test("Test 2 (Employee my-report)", "FAIL", "Employee user should NOT see 'profit' field in monthly bucket (admin-only)")
            return
    
    log_test("Test 2 (Employee my-report)", "PASS", 
             f"Employee sees is_admin=false, 8 weekly + 6 monthly buckets with invoices_count but NO profit field (admin-only)")


def test_my_report_structure():
    """Test detailed structure of my-report response"""
    print("\n" + "="*80)
    print("TEST 3: Verify detailed structure of my-report response")
    print("="*80)
    
    admin_token = login(ADMIN_CREDS)
    resp = requests.get(f"{API_BASE}/stats/my-report?weeks=2&months=2", 
                       headers=auth_headers(admin_token), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test 3 (Structure check)", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return
    
    data = resp.json()
    
    # Check weekly bucket structure in detail
    if data.get("weekly"):
        bucket = data["weekly"][0]
        
        # Verify breakdown is a dict with status keys
        if not isinstance(bucket.get("breakdown"), dict):
            log_test("Test 3 (Structure check)", "FAIL", f"Expected breakdown to be dict, got {type(bucket.get('breakdown'))}")
            return
        
        # Verify numeric fields are numbers
        numeric_fields = ["calls", "sales_count", "invoices_count", "revenue", "profit"]
        for field in numeric_fields:
            if field in bucket and not isinstance(bucket[field], (int, float)):
                log_test("Test 3 (Structure check)", "FAIL", f"Expected {field} to be numeric, got {type(bucket[field])}")
                return
    
    # Check monthly bucket structure in detail
    if data.get("monthly"):
        bucket = data["monthly"][0]
        
        # Verify breakdown is a dict
        if not isinstance(bucket.get("breakdown"), dict):
            log_test("Test 3 (Structure check)", "FAIL", f"Expected breakdown to be dict, got {type(bucket.get('breakdown'))}")
            return
        
        # Verify numeric fields are numbers
        numeric_fields = ["calls", "sales_count", "invoices_count", "revenue", "profit"]
        for field in numeric_fields:
            if field in bucket and not isinstance(bucket[field], (int, float)):
                log_test("Test 3 (Structure check)", "FAIL", f"Expected {field} to be numeric, got {type(bucket[field])}")
                return
    
    log_test("Test 3 (Structure check)", "PASS", 
             "Response structure correct: breakdown is dict, numeric fields are numbers")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("MY-REPORT ENDPOINT TESTS (with invoices and profit)")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    
    try:
        test_my_report_admin()
        test_my_report_employee()
        test_my_report_structure()
        
        print("\n" + "="*80)
        print("ALL MY-REPORT TESTS COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
