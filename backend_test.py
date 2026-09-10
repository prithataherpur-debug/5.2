#!/usr/bin/env python3
"""
Backend API Test Suite - 502 Outage Recovery Verification
Tests all core endpoints after environment reset and restoration
"""

import requests
import json
from typing import Dict, Any, Optional

# Public URL from frontend/.env
BASE_URL = "https://c5016b85-dc98-485e-b5dc-5005ae41eac1.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_CREDS = {"username": "admin", "password": "Admin@2026"}
EMP1_CREDS = {"username": "emp1", "password": "Emp@2026"}

# Test data tracking for cleanup
test_data = {
    "customers": [],
    "receipts": [],
    "sales": [],
    "invoices": []
}

def log_test(test_name: str, passed: bool, details: str = ""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"    {details}")

def login(creds: Dict[str, str]) -> Optional[str]:
    """Login and return access token"""
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json=creds, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("access_token")
        else:
            print(f"    Login failed: {resp.status_code} - {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"    Login exception: {e}")
        return None

def auth_headers(token: str) -> Dict[str, str]:
    """Return authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def cleanup():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    admin_token = login(ADMIN_CREDS)
    if not admin_token:
        print("    ⚠️  Could not get admin token for cleanup")
        return
    
    headers = auth_headers(admin_token)
    
    # Delete sales
    for sale_id in test_data["sales"]:
        try:
            requests.delete(f"{BASE_URL}/sales/{sale_id}", headers=headers, timeout=10)
        except:
            pass
    
    # Delete invoices
    for invoice_id in test_data["invoices"]:
        try:
            requests.delete(f"{BASE_URL}/invoices/{invoice_id}", headers=headers, timeout=10)
        except:
            pass
    
    # Delete receipts
    for receipt_id in test_data["receipts"]:
        try:
            requests.delete(f"{BASE_URL}/receipts/{receipt_id}", headers=headers, timeout=10)
        except:
            pass
    
    # Delete customers
    for customer_id in test_data["customers"]:
        try:
            requests.delete(f"{BASE_URL}/customers/{customer_id}", headers=headers, timeout=10)
        except:
            pass
    
    print(f"    Cleaned: {len(test_data['customers'])} customers, {len(test_data['receipts'])} receipts, {len(test_data['sales'])} sales, {len(test_data['invoices'])} invoices")

def test_auth():
    """Test authentication endpoints (PRIMARY 502 FIX VERIFICATION)"""
    print("\n" + "="*80)
    print("TEST SECTION 1: AUTHENTICATION (PRIMARY 502 FIX)")
    print("="*80)
    
    # Test 1.1: Admin login (this was returning 502)
    print("\n[1.1] POST /api/auth/login with admin credentials")
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            has_token = "access_token" in data and data["access_token"]
            has_user = "user" in data and data["user"].get("username") == "admin"
            log_test("Admin login", has_token and has_user, 
                    f"Status: {resp.status_code}, Token present: {has_token}, User: {data.get('user', {}).get('username')}")
            return data.get("access_token")
        else:
            log_test("Admin login", False, f"Status: {resp.status_code}, Body: {resp.text[:200]}")
            return None
    except Exception as e:
        log_test("Admin login", False, f"Exception: {e}")
        return None

def test_emp_login():
    """Test employee login"""
    print("\n[1.2] POST /api/auth/login with emp1 credentials")
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json=EMP1_CREDS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            has_token = "access_token" in data and data["access_token"]
            has_user = "user" in data and data["user"].get("username") == "emp1"
            log_test("Employee login", has_token and has_user,
                    f"Status: {resp.status_code}, Token present: {has_token}, User: {data.get('user', {}).get('username')}")
            return data.get("access_token")
        else:
            log_test("Employee login", False, f"Status: {resp.status_code}, Body: {resp.text[:200]}")
            return None
    except Exception as e:
        log_test("Employee login", False, f"Exception: {e}")
        return None

def test_auth_me(token: str):
    """Test GET /api/auth/me"""
    print("\n[1.3] GET /api/auth/me with admin token")
    try:
        resp = requests.get(f"{BASE_URL}/auth/me", headers=auth_headers(token), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            is_admin = data.get("username") == "admin" and data.get("role") == "admin"
            log_test("Auth /me endpoint", is_admin,
                    f"Status: {resp.status_code}, Username: {data.get('username')}, Role: {data.get('role')}")
        else:
            log_test("Auth /me endpoint", False, f"Status: {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("Auth /me endpoint", False, f"Exception: {e}")

def test_core_endpoints(token: str):
    """Test core list endpoints"""
    print("\n" + "="*80)
    print("TEST SECTION 2: CORE ENDPOINTS")
    print("="*80)
    
    headers = auth_headers(token)
    
    endpoints = [
        ("GET /api/sales", f"{BASE_URL}/sales"),
        ("GET /api/invoices", f"{BASE_URL}/invoices"),
        ("GET /api/customers/search?q=test", f"{BASE_URL}/customers/search?q=test"),
        ("GET /api/deliveries", f"{BASE_URL}/deliveries"),
        ("GET /api/stats/today", f"{BASE_URL}/stats/today"),
        ("GET /api/stats/my-report", f"{BASE_URL}/stats/my-report?weeks=8&months=6"),
    ]
    
    for idx, (name, url) in enumerate(endpoints, start=1):
        print(f"\n[2.{idx}] {name}")
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                log_test(name, True, f"Status: {resp.status_code}, Response type: {type(data).__name__}")
            else:
                log_test(name, False, f"Status: {resp.status_code}, Body: {resp.text[:200]}")
        except Exception as e:
            log_test(name, False, f"Exception: {e}")

def test_advance_credit_flow(token: str):
    """Test end-to-end advance-credit feature (DB is empty, create fresh)"""
    print("\n" + "="*80)
    print("TEST SECTION 3: ADVANCE-CREDIT FEATURE (END-TO-END)")
    print("="*80)
    
    headers = auth_headers(token)
    
    # Use unique phone number to avoid conflicts
    import time
    unique_suffix = str(int(time.time()))[-4:]
    test_phone = f"99988{unique_suffix}"
    
    # Step 1: Create customer
    print("\n[3.1] Create test customer")
    try:
        customer_data = {
            "name": "502 Recovery Test Customer",
            "phone": test_phone,
            "address": "Test Address"
        }
        resp = requests.post(f"{BASE_URL}/customers", json=customer_data, headers=headers, timeout=10)
        if resp.status_code == 200:
            customer = resp.json()
            customer_id = customer.get("id")  # Field is "id", not "customer_id"
            test_data["customers"].append(customer_id)
            log_test("Create customer", True, f"Customer ID: {customer_id}")
        else:
            log_test("Create customer", False, f"Status: {resp.status_code}, Body: {resp.text[:200]}")
            return
    except Exception as e:
        log_test("Create customer", False, f"Exception: {e}")
        return
    
    # Step 2: Create advance receipt (source_type='other', amount 3000)
    print("\n[3.2] Create advance receipt (₹3000, source_type='other')")
    try:
        receipt_data = {
            "customer_id": customer_id,
            "customer_name": "502 Recovery Test Customer",
            "customer_mobile": test_phone,
            "amount": 3000,
            "payment_mode": "cash",
            "source_type": "other",
            "narration": "Advance payment for testing"
        }
        resp = requests.post(f"{BASE_URL}/receipts", json=receipt_data, headers=headers, timeout=10)
        if resp.status_code == 200:
            receipt = resp.json()
            receipt_id = receipt.get("id")  # Field is "id", not "receipt_id"
            test_data["receipts"].append(receipt_id)
            log_test("Create advance receipt", True, 
                    f"Receipt ID: {receipt_id}, Amount: {receipt.get('amount')}, Source: {receipt.get('source_type')}")
        else:
            log_test("Create advance receipt", False, f"Status: {resp.status_code}, Body: {resp.text[:200]}")
            return
    except Exception as e:
        log_test("Create advance receipt", False, f"Exception: {e}")
        return
    
    # Step 3: Verify advance appears in GET /api/receipts/advances
    print("\n[3.3] Verify advance appears in GET /api/receipts/advances")
    try:
        resp = requests.get(f"{BASE_URL}/receipts/advances?customer_id={customer_id}", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            advances = data.get("advances", [])
            found = any(adv.get("id") == receipt_id for adv in advances)  # Field is "id"
            remaining = next((adv.get("remaining") for adv in advances if adv.get("id") == receipt_id), None)
            log_test("Advance listed", found and remaining == 3000,
                    f"Found: {found}, Remaining: {remaining}, Total amount: {data.get('total_amount')}")
        else:
            log_test("Advance listed", False, f"Status: {resp.status_code}, Body: {resp.text[:200]}")
            return
    except Exception as e:
        log_test("Advance listed", False, f"Exception: {e}")
        return
    
    # Step 4: POST /api/sales with advance_allocations:[{receipt_id, amount:800}]
    print("\n[3.4] POST /api/sales with advance_allocations (partial ₹800)")
    try:
        sale_data = {
            "customer_id": customer_id,
            "customer_name": "502 Recovery Test Customer",
            "amount": 1500,
            "product": "Test Product",
            "advance_allocations": [{"receipt_id": receipt_id, "amount": 800}]
        }
        resp = requests.post(f"{BASE_URL}/sales", json=sale_data, headers=headers, timeout=10)
        if resp.status_code == 200:
            sale = resp.json()
            sale_id = sale.get("sale_id")
            test_data["sales"].append(sale_id)
            log_test("Create sale with advance allocation", True,
                    f"Sale ID: {sale_id}, Amount: {sale.get('amount')}")
        else:
            log_test("Create sale with advance allocation", False, f"Status: {resp.status_code}, Body: {resp.text[:200]}")
            return
    except Exception as e:
        log_test("Create sale with advance allocation", False, f"Exception: {e}")
        return
    
    # Step 5: GET /api/receipts/advances must show SAME receipt with remaining=2200 (persists)
    print("\n[3.5] Verify advance persists with remaining=2200 (3000-800)")
    try:
        resp = requests.get(f"{BASE_URL}/receipts/advances?customer_id={customer_id}", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            advances = data.get("advances", [])
            found = any(adv.get("id") == receipt_id for adv in advances)  # Field is "id"
            remaining = next((adv.get("remaining") for adv in advances if adv.get("id") == receipt_id), None)
            allocated = next((adv.get("allocated") for adv in advances if adv.get("id") == receipt_id), None)
            
            persists = found and remaining == 2200 and allocated == 800
            log_test("Advance persists with correct remaining", persists,
                    f"Found: {found}, Allocated: {allocated}, Remaining: {remaining}, Total: {data.get('total_amount')}")
        else:
            log_test("Advance persists with correct remaining", False, f"Status: {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("Advance persists with correct remaining", False, f"Exception: {e}")

def main():
    """Main test runner"""
    print("\n" + "="*80)
    print("BACKEND API TEST SUITE - 502 OUTAGE RECOVERY VERIFICATION")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Testing after environment reset + restoration")
    print("="*80)
    
    try:
        # Section 1: Authentication (PRIMARY 502 FIX)
        admin_token = test_auth()
        if not admin_token:
            print("\n❌ CRITICAL: Admin login failed - cannot continue tests")
            return
        
        emp_token = test_emp_login()
        test_auth_me(admin_token)
        
        # Section 2: Core endpoints
        test_core_endpoints(admin_token)
        
        # Section 3: Advance-credit feature
        test_advance_credit_flow(admin_token)
        
    finally:
        # Cleanup
        cleanup()
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
