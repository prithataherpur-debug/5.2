#!/usr/bin/env python3
"""
Backend API test for delivery tracking feature
Tests all delivery-related endpoints with comprehensive scenarios
"""

import requests
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List

# Configuration
BASE_URL = "https://continue-here-28.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials
ADMIN_CREDS = {"username": "admin", "password": "Admin@2026"}
EMP_CREDS = {"username": "emp1", "password": "Emp@2026"}

# Global state
access_token: Optional[str] = None
created_receipt_ids: List[str] = []


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


def auth_headers() -> Dict[str, str]:
    """Return authorization headers"""
    return {"Authorization": f"Bearer {access_token}"}


def get_today_plus_days(days: int) -> str:
    """Get date string in YYYY-MM-DD format for today + days"""
    return (datetime.now(timezone.utc).date() + timedelta(days=days)).strftime("%Y-%m-%d")


def test_1_create_advance_with_delivery_default_due():
    """Test 1: CREATE ADVANCE WITH DELIVERY (default due date = TODAY+2)"""
    print("\n" + "="*80)
    print("TEST 1: Create advance receipt with delivery (default due date)")
    print("="*80)
    
    payload = {
        "customer_name": "Del Test A",
        "customer_mobile": "9990001111",
        "amount": 500,
        "payment_mode": "cash",
        "source_type": "other",
        "needs_delivery": True
    }
    
    resp = requests.post(f"{API_BASE}/receipts", json=payload, headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test 1", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return None
    
    data = resp.json()
    receipt_id = data.get("id")
    created_receipt_ids.append(receipt_id)
    
    # Verify delivery_status
    if data.get("delivery_status") != "pending":
        log_test("Test 1", "FAIL", f"Expected delivery_status='pending', got '{data.get('delivery_status')}'")
        return receipt_id
    
    # Verify delivery_due_date is TODAY+2
    expected_due = get_today_plus_days(2)
    actual_due = data.get("delivery_due_date")
    if actual_due != expected_due:
        log_test("Test 1", "FAIL", f"Expected delivery_due_date='{expected_due}', got '{actual_due}'")
        return receipt_id
    
    log_test("Test 1", "PASS", f"Receipt created with id={receipt_id}, delivery_status='pending', delivery_due_date='{actual_due}'")
    return receipt_id


def test_2_create_advance_overdue():
    """Test 2: CREATE ADVANCE OVERDUE (past due date)"""
    print("\n" + "="*80)
    print("TEST 2: Create advance receipt with overdue delivery date")
    print("="*80)
    
    payload = {
        "customer_name": "Del Test B",
        "customer_mobile": "9990002222",
        "amount": 300,
        "payment_mode": "cash",
        "source_type": "other",
        "needs_delivery": True,
        "delivery_due_date": "2020-01-01"
    }
    
    resp = requests.post(f"{API_BASE}/receipts", json=payload, headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test 2", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return None
    
    data = resp.json()
    receipt_id = data.get("id")
    created_receipt_ids.append(receipt_id)
    
    # Verify delivery_status
    if data.get("delivery_status") != "pending":
        log_test("Test 2", "FAIL", f"Expected delivery_status='pending', got '{data.get('delivery_status')}'")
        return receipt_id
    
    # Verify delivery_due_date
    if data.get("delivery_due_date") != "2020-01-01":
        log_test("Test 2", "FAIL", f"Expected delivery_due_date='2020-01-01', got '{data.get('delivery_due_date')}'")
        return receipt_id
    
    log_test("Test 2", "PASS", f"Receipt created with id={receipt_id}, delivery_status='pending', delivery_due_date='2020-01-01'")
    return receipt_id


def test_3_list_pending_deliveries(id1: str, id2: str):
    """Test 3: LIST PENDING deliveries with overdue flag and sorting"""
    print("\n" + "="*80)
    print("TEST 3: List pending deliveries")
    print("="*80)
    
    resp = requests.get(f"{API_BASE}/deliveries?status=pending", headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test 3", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return
    
    data = resp.json()
    
    # Verify response structure
    required_keys = ["date", "count", "pending_count", "overdue_count", "deliveries"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        log_test("Test 3", "FAIL", f"Missing keys in response: {missing_keys}")
        return
    
    deliveries = data.get("deliveries", [])
    
    # Verify both receipts are present
    delivery_ids = [d.get("id") for d in deliveries]
    if id1 not in delivery_ids:
        log_test("Test 3", "FAIL", f"Receipt {id1} not found in pending deliveries")
        return
    if id2 not in delivery_ids:
        log_test("Test 3", "FAIL", f"Receipt {id2} not found in pending deliveries")
        return
    
    # Verify overdue flag for id2 (2020-01-01)
    id2_delivery = next((d for d in deliveries if d.get("id") == id2), None)
    if not id2_delivery:
        log_test("Test 3", "FAIL", f"Receipt {id2} not found in deliveries list")
        return
    
    if not id2_delivery.get("overdue"):
        log_test("Test 3", "FAIL", f"Receipt {id2} should have overdue=true, got {id2_delivery.get('overdue')}")
        return
    
    # Verify sorting (oldest/overdue first)
    due_dates = [d.get("delivery_due_date") for d in deliveries if d.get("delivery_due_date")]
    if due_dates != sorted(due_dates):
        log_test("Test 3", "FAIL", f"Deliveries not sorted by due date ascending. Got: {due_dates}")
        return
    
    # Verify overdue_count >= 1
    if data.get("overdue_count", 0) < 1:
        log_test("Test 3", "FAIL", f"Expected overdue_count >= 1, got {data.get('overdue_count')}")
        return
    
    log_test("Test 3", "PASS", 
             f"Found {data['count']} deliveries, {data['pending_count']} pending, {data['overdue_count']} overdue. "
             f"Both test receipts present, overdue flag correct, sorted by due date.")


def test_4_mark_delivered(receipt_id: str):
    """Test 4: MARK DELIVERED"""
    print("\n" + "="*80)
    print("TEST 4: Mark delivery as delivered")
    print("="*80)
    
    payload = {
        "mark_delivered": True,
        "delivery_note": "Handed over"
    }
    
    resp = requests.patch(f"{API_BASE}/deliveries/{receipt_id}", json=payload, headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test 4", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return
    
    data = resp.json()
    
    # Verify delivery_status
    if data.get("delivery_status") != "delivered":
        log_test("Test 4", "FAIL", f"Expected delivery_status='delivered', got '{data.get('delivery_status')}'")
        return
    
    # Verify delivered_at is set
    if not data.get("delivered_at"):
        log_test("Test 4", "FAIL", "Expected delivered_at to be set (non-null)")
        return
    
    # Verify delivery_note
    if data.get("delivery_note") != "Handed over":
        log_test("Test 4", "FAIL", f"Expected delivery_note='Handed over', got '{data.get('delivery_note')}'")
        return
    
    # Verify it's NOT in pending list
    resp_pending = requests.get(f"{API_BASE}/deliveries?status=pending", headers=auth_headers(), timeout=10)
    if resp_pending.status_code == 200:
        pending_ids = [d.get("id") for d in resp_pending.json().get("deliveries", [])]
        if receipt_id in pending_ids:
            log_test("Test 4", "FAIL", f"Receipt {receipt_id} still appears in pending list after marking delivered")
            return
    
    # Verify it IS in delivered list
    resp_delivered = requests.get(f"{API_BASE}/deliveries?status=delivered", headers=auth_headers(), timeout=10)
    if resp_delivered.status_code == 200:
        delivered_ids = [d.get("id") for d in resp_delivered.json().get("deliveries", [])]
        if receipt_id not in delivered_ids:
            log_test("Test 4", "FAIL", f"Receipt {receipt_id} not found in delivered list after marking delivered")
            return
    
    log_test("Test 4", "PASS", 
             f"Receipt {receipt_id} marked as delivered, delivered_at set, delivery_note='Handed over', "
             f"removed from pending list, appears in delivered list")


def test_5_update_due_date(receipt_id: str):
    """Test 5: UPDATE DUE DATE"""
    print("\n" + "="*80)
    print("TEST 5: Update delivery due date")
    print("="*80)
    
    payload = {
        "delivery_due_date": "2030-05-05"
    }
    
    resp = requests.patch(f"{API_BASE}/deliveries/{receipt_id}", json=payload, headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test 5", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return
    
    data = resp.json()
    
    # Verify delivery_due_date
    if data.get("delivery_due_date") != "2030-05-05":
        log_test("Test 5", "FAIL", f"Expected delivery_due_date='2030-05-05', got '{data.get('delivery_due_date')}'")
        return
    
    log_test("Test 5", "PASS", f"Receipt {receipt_id} due date updated to '2030-05-05'")


def test_6_regression_normal_receipt():
    """Test 6: REGRESSION - normal receipt without delivery"""
    print("\n" + "="*80)
    print("TEST 6: Regression - normal receipt (no delivery)")
    print("="*80)
    
    payload = {
        "customer_name": "No Del",
        "customer_mobile": "9990003333",
        "amount": 200,
        "payment_mode": "cash",
        "source_type": "other"
    }
    
    resp = requests.post(f"{API_BASE}/receipts", json=payload, headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test 6", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return None
    
    data = resp.json()
    receipt_id = data.get("id")
    created_receipt_ids.append(receipt_id)
    
    # Verify delivery_status is "none"
    if data.get("delivery_status") != "none":
        log_test("Test 6", "FAIL", f"Expected delivery_status='none', got '{data.get('delivery_status')}'")
        return receipt_id
    
    # Verify it does NOT appear in pending deliveries
    resp_pending = requests.get(f"{API_BASE}/deliveries?status=pending", headers=auth_headers(), timeout=10)
    if resp_pending.status_code == 200:
        pending_ids = [d.get("id") for d in resp_pending.json().get("deliveries", [])]
        if receipt_id in pending_ids:
            log_test("Test 6", "FAIL", f"Receipt {receipt_id} with delivery_status='none' should NOT appear in pending deliveries")
            return receipt_id
    
    log_test("Test 6", "PASS", f"Normal receipt created with id={receipt_id}, delivery_status='none', not in pending list")
    return receipt_id


def test_7_regression_spot_checks():
    """Test 7: REGRESSION - spot check other endpoints"""
    print("\n" + "="*80)
    print("TEST 7: Regression - spot check GET /api/receipts and /api/receipts/advances")
    print("="*80)
    
    # Test GET /api/receipts
    resp = requests.get(f"{API_BASE}/receipts?limit=5", headers=auth_headers(), timeout=10)
    if resp.status_code != 200:
        log_test("Test 7a (GET /api/receipts)", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
    else:
        data = resp.json()
        if not isinstance(data, list):
            log_test("Test 7a (GET /api/receipts)", "FAIL", f"Expected array response, got {type(data)}")
        else:
            log_test("Test 7a (GET /api/receipts)", "PASS", f"Returns array with {len(data)} receipts")
    
    # Test GET /api/receipts/advances
    resp = requests.get(f"{API_BASE}/receipts/advances?phone=9990003333", headers=auth_headers(), timeout=10)
    if resp.status_code != 200:
        log_test("Test 7b (GET /api/receipts/advances)", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
    else:
        data = resp.json()
        if "advances" not in data:
            log_test("Test 7b (GET /api/receipts/advances)", "FAIL", f"Expected 'advances' key in response, got {data.keys()}")
        else:
            log_test("Test 7b (GET /api/receipts/advances)", "PASS", f"Returns advances array with {len(data['advances'])} items")


def test_8_validation_errors():
    """Test 8: VALIDATION - error cases"""
    print("\n" + "="*80)
    print("TEST 8: Validation - error cases")
    print("="*80)
    
    # Test 8a: Invalid date format
    if created_receipt_ids:
        payload = {"delivery_due_date": "not-a-date"}
        resp = requests.patch(f"{API_BASE}/deliveries/{created_receipt_ids[0]}", json=payload, headers=auth_headers(), timeout=10)
        if resp.status_code != 400:
            log_test("Test 8a (invalid date)", "FAIL", f"Expected 400, got {resp.status_code}")
        else:
            log_test("Test 8a (invalid date)", "PASS", "Returns 400 for invalid date format")
    
    # Test 8b: Nonexistent receipt ID
    payload = {"mark_delivered": True}
    resp = requests.patch(f"{API_BASE}/deliveries/nonexistent-id-12345", json=payload, headers=auth_headers(), timeout=10)
    if resp.status_code != 404:
        log_test("Test 8b (nonexistent ID)", "FAIL", f"Expected 404, got {resp.status_code}")
    else:
        log_test("Test 8b (nonexistent ID)", "PASS", "Returns 404 for nonexistent receipt ID")


def cleanup():
    """Delete all test receipts"""
    print("\n" + "="*80)
    print("CLEANUP: Deleting test receipts")
    print("="*80)
    
    deleted_count = 0
    failed_count = 0
    
    for receipt_id in created_receipt_ids:
        try:
            resp = requests.delete(f"{API_BASE}/receipts/{receipt_id}", headers=auth_headers(), timeout=10)
            if resp.status_code in [200, 204]:
                deleted_count += 1
                print(f"   ✅ Deleted receipt {receipt_id}")
            else:
                failed_count += 1
                print(f"   ⚠️  Failed to delete receipt {receipt_id}: {resp.status_code}")
        except Exception as e:
            failed_count += 1
            print(f"   ⚠️  Error deleting receipt {receipt_id}: {e}")
    
    print(f"\nCleanup complete: {deleted_count} deleted, {failed_count} failed")


def main():
    """Run all tests"""
    global access_token
    
    print("\n" + "="*80)
    print("DELIVERY TRACKING BACKEND API TESTS")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    
    try:
        # Login
        print("\n" + "="*80)
        print("AUTHENTICATION")
        print("="*80)
        access_token = login(ADMIN_CREDS)
        print(f"✅ Logged in as admin")
        
        # Run tests
        id1 = test_1_create_advance_with_delivery_default_due()
        id2 = test_2_create_advance_overdue()
        
        if id1 and id2:
            test_3_list_pending_deliveries(id1, id2)
        
        if id1:
            test_4_mark_delivered(id1)
        
        if id2:
            test_5_update_due_date(id2)
        
        test_6_regression_normal_receipt()
        test_7_regression_spot_checks()
        test_8_validation_errors()
        
        # Cleanup
        cleanup()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Attempt cleanup even on error
        if created_receipt_ids:
            print("\nAttempting cleanup after error...")
            cleanup()


if __name__ == "__main__":
    main()
