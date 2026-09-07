#!/usr/bin/env python3
"""
Backend smoke/regression test after deployment fix.
Tests health, auth, and key endpoints to ensure nothing regressed.
"""

import requests
import json
import sys

# Use the external ingress URL
BASE_URL = "https://code-launcher-122.preview.emergentagent.com"

# Test credentials from /app/memory/test_credentials.md
ADMIN_CREDS = {"username": "admin", "password": "Admin@2026"}
EMP1_CREDS = {"username": "emp1", "password": "Emp@2026"}

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

test_results = []

def log_pass(test_name, details=""):
    print(f"{GREEN}✓ PASS{RESET}: {test_name}")
    if details:
        print(f"  {details}")
    test_results.append({"test": test_name, "status": "PASS", "details": details})

def log_fail(test_name, details=""):
    print(f"{RED}✗ FAIL{RESET}: {test_name}")
    if details:
        print(f"  {details}")
    test_results.append({"test": test_name, "status": "FAIL", "details": details})

def log_info(message):
    print(f"{YELLOW}ℹ{RESET} {message}")

def test_health_endpoint():
    """Test 1: GET /health (or GET /) responds 200 and DB is connected"""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)
    
    # Test GET /health
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        if resp.status_code == 200:
            log_pass("GET /health", f"Status: {resp.status_code}, Response: {resp.text[:100]}")
        else:
            log_fail("GET /health", f"Expected 200, got {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log_fail("GET /health", f"Exception: {str(e)}")
    
    # Test GET / (root) - Note: public URL routes only /api/* to backend
    # The root / returns Expo HTML, not backend JSON. This is expected.
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=10)
        if resp.status_code == 200:
            # Public URL returns Expo HTML at root, not backend JSON
            log_pass("GET / (root)", f"Status: {resp.status_code} (Note: public URL returns Expo HTML, not backend JSON - this is expected)")
        else:
            log_fail("GET / (root)", f"Expected 200, got {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log_fail("GET / (root)", f"Exception: {str(e)}")

def test_auth_login():
    """Test 2: POST /api/auth/login works for BOTH admin and emp1"""
    print("\n" + "="*70)
    print("TEST 2: Authentication")
    print("="*70)
    
    tokens = {}
    
    # Test admin login
    try:
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "access_token" in data and "user" in data:
                tokens["admin"] = data["access_token"]
                user = data["user"]
                log_pass("POST /api/auth/login (admin)", 
                        f"Token received, User: {user.get('username')}, Role: {user.get('role')}")
            else:
                log_fail("POST /api/auth/login (admin)", f"Missing access_token or user in response: {json.dumps(data)}")
        else:
            log_fail("POST /api/auth/login (admin)", f"Expected 200, got {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log_fail("POST /api/auth/login (admin)", f"Exception: {str(e)}")
    
    # Test emp1 login
    try:
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=EMP1_CREDS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "access_token" in data and "user" in data:
                tokens["emp1"] = data["access_token"]
                user = data["user"]
                log_pass("POST /api/auth/login (emp1)", 
                        f"Token received, User: {user.get('username')}, Role: {user.get('role')}")
            else:
                log_fail("POST /api/auth/login (emp1)", f"Missing access_token or user in response: {json.dumps(data)}")
        else:
            log_fail("POST /api/auth/login (emp1)", f"Expected 200, got {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log_fail("POST /api/auth/login (emp1)", f"Exception: {str(e)}")
    
    return tokens

def test_my_report_emp1(token):
    """Test 3: GET /api/stats/my-report with emp1 token"""
    print("\n" + "="*70)
    print("TEST 3: My Report Endpoint (emp1)")
    print("="*70)
    
    if not token:
        log_fail("GET /api/stats/my-report (emp1)", "No token available (login failed)")
        return
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/api/stats/my-report?weeks=8&months=6", 
                          headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            
            # Validate structure
            if "weekly" not in data or "monthly" not in data:
                log_fail("GET /api/stats/my-report (emp1)", 
                        f"Missing 'weekly' or 'monthly' in response: {json.dumps(data)[:200]}")
                return
            
            weekly = data.get("weekly", [])
            monthly = data.get("monthly", [])
            
            # Check weekly buckets
            if len(weekly) != 8:
                log_fail("GET /api/stats/my-report (emp1)", 
                        f"Expected 8 weekly buckets, got {len(weekly)}")
                return
            
            # Check monthly buckets
            if len(monthly) != 6:
                log_fail("GET /api/stats/my-report (emp1)", 
                        f"Expected 6 monthly buckets, got {len(monthly)}")
                return
            
            # Validate bucket structure
            sample_week = weekly[0] if weekly else {}
            required_fields = ["calls", "breakdown", "sales_count", "revenue"]
            missing_fields = [f for f in required_fields if f not in sample_week]
            
            if missing_fields:
                log_fail("GET /api/stats/my-report (emp1)", 
                        f"Weekly bucket missing fields: {missing_fields}. Sample: {json.dumps(sample_week)}")
                return
            
            # Check username is emp1
            if data.get("username") != "emp1":
                log_fail("GET /api/stats/my-report (emp1)", 
                        f"Expected username 'emp1', got '{data.get('username')}'")
                return
            
            log_pass("GET /api/stats/my-report (emp1)", 
                    f"Returns 8 weekly + 6 monthly buckets for user 'emp1'. "
                    f"Sample weekly: calls={sample_week.get('calls')}, sales={sample_week.get('sales_count')}, "
                    f"revenue={sample_week.get('revenue')}")
        else:
            log_fail("GET /api/stats/my-report (emp1)", 
                    f"Expected 200, got {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log_fail("GET /api/stats/my-report (emp1)", f"Exception: {str(e)}")

def test_my_report_admin(token):
    """Test 4: GET /api/stats/my-report with admin token"""
    print("\n" + "="*70)
    print("TEST 4: My Report Endpoint (admin)")
    print("="*70)
    
    if not token:
        log_fail("GET /api/stats/my-report (admin)", "No token available (login failed)")
        return
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/api/stats/my-report?weeks=8&months=6", 
                          headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            
            # Validate structure
            if "weekly" not in data or "monthly" not in data:
                log_fail("GET /api/stats/my-report (admin)", 
                        f"Missing 'weekly' or 'monthly' in response: {json.dumps(data)[:200]}")
                return
            
            weekly = data.get("weekly", [])
            monthly = data.get("monthly", [])
            
            # Check weekly buckets
            if len(weekly) != 8:
                log_fail("GET /api/stats/my-report (admin)", 
                        f"Expected 8 weekly buckets, got {len(weekly)}")
                return
            
            # Check monthly buckets
            if len(monthly) != 6:
                log_fail("GET /api/stats/my-report (admin)", 
                        f"Expected 6 monthly buckets, got {len(monthly)}")
                return
            
            # Check username is admin
            if data.get("username") != "admin":
                log_fail("GET /api/stats/my-report (admin)", 
                        f"Expected username 'admin', got '{data.get('username')}'")
                return
            
            sample_week = weekly[0] if weekly else {}
            log_pass("GET /api/stats/my-report (admin)", 
                    f"Returns 8 weekly + 6 monthly buckets for user 'admin'. "
                    f"Sample weekly: calls={sample_week.get('calls')}, sales={sample_week.get('sales_count')}, "
                    f"revenue={sample_week.get('revenue')}")
        else:
            log_fail("GET /api/stats/my-report (admin)", 
                    f"Expected 200, got {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log_fail("GET /api/stats/my-report (admin)", f"Exception: {str(e)}")

def test_spot_checks(token):
    """Test 5: Spot-check existing endpoints (stats/today, stats/leaderboard)"""
    print("\n" + "="*70)
    print("TEST 5: Spot Checks (Regression)")
    print("="*70)
    
    if not token:
        log_fail("Spot checks", "No token available (login failed)")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET /api/stats/today
    try:
        resp = requests.get(f"{BASE_URL}/api/stats/today", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            required_fields = ["date", "goal", "total_calls", "breakdown", "pending_customers", "total_customers"]
            missing = [f for f in required_fields if f not in data]
            if missing:
                log_fail("GET /api/stats/today", f"Missing fields: {missing}. Response: {json.dumps(data)[:200]}")
            else:
                log_pass("GET /api/stats/today", 
                        f"Returns expected structure. Total calls: {data.get('total_calls')}, "
                        f"Goal: {data.get('goal')}, Pending: {data.get('pending_customers')}")
        else:
            log_fail("GET /api/stats/today", f"Expected 200, got {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log_fail("GET /api/stats/today", f"Exception: {str(e)}")
    
    # Test GET /api/stats/leaderboard
    try:
        resp = requests.get(f"{BASE_URL}/api/stats/leaderboard", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # The endpoint returns {"date": ..., "goal": ..., "rows": [...]}
            if "rows" in data and isinstance(data["rows"], list):
                log_pass("GET /api/stats/leaderboard", 
                        f"Returns leaderboard with {len(data['rows'])} entries. Date: {data.get('date')}")
            else:
                log_fail("GET /api/stats/leaderboard", 
                        f"Expected 'rows' array in response: {json.dumps(data)[:200]}")
        else:
            log_fail("GET /api/stats/leaderboard", f"Expected 200, got {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log_fail("GET /api/stats/leaderboard", f"Exception: {str(e)}")

def print_summary():
    """Print test summary"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")
    
    if failed > 0:
        print(f"\n{RED}FAILED TESTS:{RESET}")
        for r in test_results:
            if r["status"] == "FAIL":
                print(f"  ✗ {r['test']}")
                if r["details"]:
                    print(f"    {r['details']}")
    
    print("\n" + "="*70)
    
    return failed == 0

def main():
    print("="*70)
    print("BACKEND SMOKE/REGRESSION TEST")
    print("After deployment fix: removed quotes from backend/.env")
    print("="*70)
    log_info(f"Base URL: {BASE_URL}")
    log_info("Testing: health, auth, my-report, stats endpoints")
    
    # Run tests
    test_health_endpoint()
    tokens = test_auth_login()
    test_my_report_emp1(tokens.get("emp1"))
    test_my_report_admin(tokens.get("admin"))
    test_spot_checks(tokens.get("emp1"))  # Use emp1 token for spot checks
    
    # Print summary
    success = print_summary()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
