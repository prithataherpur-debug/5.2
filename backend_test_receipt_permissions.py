#!/usr/bin/env python3
"""
Backend API Test Suite - Money Receipt Edit Permission Test
Tests owner-or-admin permission on PATCH/PUT /receipts/{rid}; DELETE stays admin-only
"""

import requests
import json
from typing import Dict, Any, Optional

# Public URL from review request
BASE_URL = "https://c5016b85-dc98-485e-b5dc-5005ae41eac1.preview.emergentagent.com/api"

# Test credentials
ADMIN_CREDS = {"username": "admin", "password": "Admin@2026"}
EMP1_CREDS = {"username": "emp1", "password": "Emp@2026"}
EMP2_CREDS = {"username": "emp2", "password": "Emp@2026"}

# Test data tracking for cleanup
test_data = {
    "customers": [],
    "receipts": [],
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
    
    print(f"    Cleaned: {len(test_data['customers'])} customers, {len(test_data['receipts'])} receipts")

def test_receipt_edit_permissions():
    """Test money-receipt edit permission: owner OR admin can PATCH/PUT; DELETE is admin-only"""
    print("\n" + "="*80)
    print("MONEY-RECEIPT EDIT PERMISSION TEST")
    print("="*80)
    print("Testing: PATCH/PUT /receipts/{rid} allow owner OR admin")
    print("         DELETE /receipts/{rid} is admin-only")
    print("="*80)
    
    # Get tokens for all users
    print("\n[SETUP] Getting auth tokens...")
    admin_token = login(ADMIN_CREDS)
    emp1_token = login(EMP1_CREDS)
    emp2_token = login(EMP2_CREDS)
    
    if not all([admin_token, emp1_token, emp2_token]):
        print("❌ CRITICAL: Could not get all auth tokens")
        return
    
    print("    ✅ Got tokens for admin, emp1, emp2")
    
    # Use unique phone to avoid conflicts
    import time
    unique_suffix = str(int(time.time()))[-4:]
    test_phone = f"99977{unique_suffix}"
    
    # SCENARIO 1: emp1 creates a money receipt
    print("\n" + "="*80)
    print("SCENARIO 1: emp1 creates a money receipt")
    print("="*80)
    
    emp1_headers = auth_headers(emp1_token)
    
    receipt_data = {
        "customer_name": "Receipt Permission Test Customer",
        "customer_mobile": test_phone,
        "amount": 5000,
        "payment_mode": "cash",
        "source_type": "other",
        "narration": "Initial receipt for permission testing"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/receipts", json=receipt_data, headers=emp1_headers, timeout=10)
        if resp.status_code == 200:
            receipt = resp.json()
            receipt_id = receipt.get("id")
            customer_id = receipt.get("customer_id")
            test_data["receipts"].append(receipt_id)
            if customer_id:
                test_data["customers"].append(customer_id)
            log_test("emp1 creates receipt", True, 
                    f"Receipt ID: {receipt_id}, Amount: {receipt.get('amount')}, User: {receipt.get('user')}")
        else:
            log_test("emp1 creates receipt", False, f"Status: {resp.status_code}, Body: {resp.text[:200]}")
            return
    except Exception as e:
        log_test("emp1 creates receipt", False, f"Exception: {e}")
        return
    
    # SCENARIO 2: emp1 edits their OWN receipt (PATCH)
    print("\n" + "="*80)
    print("SCENARIO 2: emp1 edits their OWN receipt (PATCH)")
    print("="*80)
    
    try:
        patch_data = {"narration": "edited by owner (emp1)"}
        resp = requests.patch(f"{BASE_URL}/receipts/{receipt_id}", json=patch_data, headers=emp1_headers, timeout=10)
        
        if resp.status_code == 200:
            updated = resp.json()
            narration_updated = updated.get("narration") == "edited by owner (emp1)"
            log_test("emp1 PATCH own receipt", narration_updated,
                    f"Status: {resp.status_code}, Narration: {updated.get('narration')}")
        else:
            log_test("emp1 PATCH own receipt", False, 
                    f"Expected 200, got {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("emp1 PATCH own receipt", False, f"Exception: {e}")
    
    # SCENARIO 2b: emp1 edits their OWN receipt (PUT)
    print("\n" + "="*80)
    print("SCENARIO 2b: emp1 edits their OWN receipt (PUT)")
    print("="*80)
    
    try:
        put_data = {
            "customer_name": "Receipt Permission Test Customer",
            "customer_mobile": test_phone,
            "amount": 5000,
            "payment_mode": "cash",
            "source_type": "other",
            "narration": "fully replaced by owner (emp1)"
        }
        resp = requests.put(f"{BASE_URL}/receipts/{receipt_id}", json=put_data, headers=emp1_headers, timeout=10)
        
        if resp.status_code == 200:
            updated = resp.json()
            narration_updated = updated.get("narration") == "fully replaced by owner (emp1)"
            pdf_regenerated = updated.get("pdf_token") is not None
            log_test("emp1 PUT own receipt", narration_updated and pdf_regenerated,
                    f"Status: {resp.status_code}, Narration: {updated.get('narration')}, PDF token present: {pdf_regenerated}")
        else:
            log_test("emp1 PUT own receipt", False,
                    f"Expected 200, got {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("emp1 PUT own receipt", False, f"Exception: {e}")
    
    # SCENARIO 3: emp2 (different non-admin) tries to edit emp1's receipt (PATCH)
    print("\n" + "="*80)
    print("SCENARIO 3: emp2 tries to edit emp1's receipt (PATCH)")
    print("="*80)
    
    emp2_headers = auth_headers(emp2_token)
    
    try:
        patch_data = {"narration": "attempted edit by emp2"}
        resp = requests.patch(f"{BASE_URL}/receipts/{receipt_id}", json=patch_data, headers=emp2_headers, timeout=10)
        
        if resp.status_code == 403:
            log_test("emp2 PATCH emp1's receipt → 403", True,
                    f"Status: {resp.status_code} (correctly forbidden)")
        else:
            log_test("emp2 PATCH emp1's receipt → 403", False,
                    f"Expected 403, got {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("emp2 PATCH emp1's receipt → 403", False, f"Exception: {e}")
    
    # SCENARIO 3b: emp2 tries to edit emp1's receipt (PUT)
    print("\n" + "="*80)
    print("SCENARIO 3b: emp2 tries to edit emp1's receipt (PUT)")
    print("="*80)
    
    try:
        put_data = {
            "customer_name": "Receipt Permission Test Customer",
            "customer_mobile": test_phone,
            "amount": 5000,
            "payment_mode": "cash",
            "source_type": "other",
            "narration": "attempted full replace by emp2"
        }
        resp = requests.put(f"{BASE_URL}/receipts/{receipt_id}", json=put_data, headers=emp2_headers, timeout=10)
        
        if resp.status_code == 403:
            log_test("emp2 PUT emp1's receipt → 403", True,
                    f"Status: {resp.status_code} (correctly forbidden)")
        else:
            log_test("emp2 PUT emp1's receipt → 403", False,
                    f"Expected 403, got {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("emp2 PUT emp1's receipt → 403", False, f"Exception: {e}")
    
    # SCENARIO 4: admin edits emp1's receipt (PATCH)
    print("\n" + "="*80)
    print("SCENARIO 4: admin edits emp1's receipt (PATCH)")
    print("="*80)
    
    admin_headers = auth_headers(admin_token)
    
    try:
        patch_data = {"narration": "edited by admin"}
        resp = requests.patch(f"{BASE_URL}/receipts/{receipt_id}", json=patch_data, headers=admin_headers, timeout=10)
        
        if resp.status_code == 200:
            updated = resp.json()
            narration_updated = updated.get("narration") == "edited by admin"
            log_test("admin PATCH emp1's receipt", narration_updated,
                    f"Status: {resp.status_code}, Narration: {updated.get('narration')}")
        else:
            log_test("admin PATCH emp1's receipt", False,
                    f"Expected 200, got {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("admin PATCH emp1's receipt", False, f"Exception: {e}")
    
    # SCENARIO 4b: admin edits emp1's receipt (PUT)
    print("\n" + "="*80)
    print("SCENARIO 4b: admin edits emp1's receipt (PUT)")
    print("="*80)
    
    try:
        put_data = {
            "customer_name": "Receipt Permission Test Customer",
            "customer_mobile": test_phone,
            "amount": 5000,
            "payment_mode": "cash",
            "source_type": "other",
            "narration": "fully replaced by admin"
        }
        resp = requests.put(f"{BASE_URL}/receipts/{receipt_id}", json=put_data, headers=admin_headers, timeout=10)
        
        if resp.status_code == 200:
            updated = resp.json()
            narration_updated = updated.get("narration") == "fully replaced by admin"
            pdf_regenerated = updated.get("pdf_token") is not None
            log_test("admin PUT emp1's receipt", narration_updated and pdf_regenerated,
                    f"Status: {resp.status_code}, Narration: {updated.get('narration')}, PDF token present: {pdf_regenerated}")
        else:
            log_test("admin PUT emp1's receipt", False,
                    f"Expected 200, got {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("admin PUT emp1's receipt", False, f"Exception: {e}")
    
    # SCENARIO 5: emp1 tries DELETE their own receipt → 403 (admin-only)
    print("\n" + "="*80)
    print("SCENARIO 5: emp1 tries DELETE their own receipt → 403")
    print("="*80)
    
    try:
        resp = requests.delete(f"{BASE_URL}/receipts/{receipt_id}", headers=emp1_headers, timeout=10)
        
        if resp.status_code == 403:
            log_test("emp1 DELETE own receipt → 403", True,
                    f"Status: {resp.status_code} (correctly forbidden - delete is admin-only)")
        else:
            log_test("emp1 DELETE own receipt → 403", False,
                    f"Expected 403, got {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("emp1 DELETE own receipt → 403", False, f"Exception: {e}")
    
    # SCENARIO 6: admin DELETE emp1's receipt → 200 (cleanup)
    print("\n" + "="*80)
    print("SCENARIO 6: admin DELETE emp1's receipt → 200")
    print("="*80)
    
    try:
        resp = requests.delete(f"{BASE_URL}/receipts/{receipt_id}", headers=admin_headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            deleted = data.get("deleted") == True
            log_test("admin DELETE receipt", deleted,
                    f"Status: {resp.status_code}, Deleted: {deleted}")
            # Remove from cleanup list since we just deleted it
            if receipt_id in test_data["receipts"]:
                test_data["receipts"].remove(receipt_id)
        else:
            log_test("admin DELETE receipt", False,
                    f"Expected 200, got {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("admin DELETE receipt", False, f"Exception: {e}")
    
    # SCENARIO 7: Regression tests
    print("\n" + "="*80)
    print("SCENARIO 7: Regression tests")
    print("="*80)
    
    # 7a: POST /api/receipts still works
    print("\n[7a] POST /api/receipts still works")
    try:
        receipt_data = {
            "customer_name": "Regression Test Customer",
            "customer_mobile": f"99966{unique_suffix}",
            "amount": 1000,
            "payment_mode": "cash",
            "source_type": "other"
        }
        resp = requests.post(f"{BASE_URL}/receipts", json=receipt_data, headers=emp1_headers, timeout=10)
        
        if resp.status_code == 200:
            receipt = resp.json()
            new_receipt_id = receipt.get("id")
            new_customer_id = receipt.get("customer_id")
            test_data["receipts"].append(new_receipt_id)
            if new_customer_id:
                test_data["customers"].append(new_customer_id)
            log_test("POST /api/receipts regression", True,
                    f"Status: {resp.status_code}, Receipt ID: {new_receipt_id}")
        else:
            log_test("POST /api/receipts regression", False,
                    f"Status: {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("POST /api/receipts regression", False, f"Exception: {e}")
    
    # 7b: GET /api/receipts still works
    print("\n[7b] GET /api/receipts still works")
    try:
        resp = requests.get(f"{BASE_URL}/receipts", headers=admin_headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            is_array = isinstance(data, list)
            log_test("GET /api/receipts regression", is_array,
                    f"Status: {resp.status_code}, Response is array: {is_array}")
        else:
            log_test("GET /api/receipts regression", False,
                    f"Status: {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("GET /api/receipts regression", False, f"Exception: {e}")
    
    # 7c: GET /api/receipts/advances still works
    print("\n[7c] GET /api/receipts/advances still works")
    try:
        resp = requests.get(f"{BASE_URL}/receipts/advances", headers=admin_headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            has_advances = "advances" in data
            log_test("GET /api/receipts/advances regression", has_advances,
                    f"Status: {resp.status_code}, Has 'advances' key: {has_advances}")
        else:
            log_test("GET /api/receipts/advances regression", False,
                    f"Status: {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_test("GET /api/receipts/advances regression", False, f"Exception: {e}")

def main():
    """Main test runner"""
    print("\n" + "="*80)
    print("BACKEND API TEST SUITE - MONEY-RECEIPT EDIT PERMISSION")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Testing: Owner OR admin can PATCH/PUT receipts; DELETE is admin-only")
    print("="*80)
    
    try:
        test_receipt_edit_permissions()
    finally:
        cleanup()
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
