#!/usr/bin/env python3
"""
Backend API test for sale creation with purchase_amount and attach_receipt_ids
Tests all scenarios for the new optional fields on POST /api/sales
"""

import requests
import json
from typing import Optional, Dict, List

# Configuration
BASE_URL = "https://open-hub-15.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials
ADMIN_CREDS = {"username": "admin", "password": "Admin@2026"}
EMP_CREDS = {"username": "emp1", "password": "Emp@2026"}

# Global state
access_token: Optional[str] = None
created_customer_ids: List[str] = []
created_receipt_ids: List[str] = []
created_sale_ids: List[str] = []


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


# ============================================================================
# (A) PURCHASE COST TESTS
# ============================================================================

def test_a1_sale_with_purchase_amount():
    """Test A.1: POST /api/sales with purchase_amount → expect purchase_amount=600 and profit=400"""
    print("\n" + "="*80)
    print("TEST A.1: Create sale with purchase_amount")
    print("="*80)
    
    payload = {
        "customer_name": "Cost Test Customer",
        "amount": 1000,
        "product": "Product X",
        "purchase_amount": 600
    }
    
    resp = requests.post(f"{API_BASE}/sales", json=payload, headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test A.1", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return None
    
    data = resp.json()
    sale_id = data.get("id")
    created_sale_ids.append(sale_id)
    
    # Verify purchase_amount
    if data.get("purchase_amount") != 600:
        log_test("Test A.1", "FAIL", f"Expected purchase_amount=600, got {data.get('purchase_amount')}")
        return sale_id
    
    # Verify profit = amount - purchase_amount = 1000 - 600 = 400
    if data.get("profit") != 400:
        log_test("Test A.1", "FAIL", f"Expected profit=400, got {data.get('profit')}")
        return sale_id
    
    log_test("Test A.1", "PASS", 
             f"Sale created with id={sale_id}, purchase_amount=600, profit=400")
    return sale_id


def test_a2_sale_with_negative_purchase_amount():
    """Test A.2: POST /api/sales with purchase_amount=-5 → expect 400"""
    print("\n" + "="*80)
    print("TEST A.2: Create sale with negative purchase_amount (should fail)")
    print("="*80)
    
    payload = {
        "customer_name": "Negative Cost Test",
        "amount": 1000,
        "product": "Product Y",
        "purchase_amount": -5
    }
    
    resp = requests.post(f"{API_BASE}/sales", json=payload, headers=auth_headers(), timeout=10)
    
    if resp.status_code != 400:
        log_test("Test A.2", "FAIL", f"Expected 400, got {resp.status_code}: {resp.text}")
        return
    
    log_test("Test A.2", "PASS", "Correctly rejected negative purchase_amount with 400 error")


def test_a3_sale_without_purchase_amount():
    """Test A.3: POST /api/sales without purchase_amount → expect 200 and purchase_amount=null (regression)"""
    print("\n" + "="*80)
    print("TEST A.3: Create sale without purchase_amount (regression)")
    print("="*80)
    
    payload = {
        "customer_name": "No Cost Customer",
        "amount": 1000,
        "product": "Product Z"
    }
    
    resp = requests.post(f"{API_BASE}/sales", json=payload, headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test A.3", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return None
    
    data = resp.json()
    sale_id = data.get("id")
    created_sale_ids.append(sale_id)
    
    # Verify purchase_amount is null
    if data.get("purchase_amount") is not None:
        log_test("Test A.3", "FAIL", f"Expected purchase_amount=null, got {data.get('purchase_amount')}")
        return sale_id
    
    # Verify profit = amount (since no purchase_amount)
    if data.get("profit") != 1000:
        log_test("Test A.3", "FAIL", f"Expected profit=1000, got {data.get('profit')}")
        return sale_id
    
    log_test("Test A.3", "PASS", 
             f"Sale created with id={sale_id}, purchase_amount=null, profit=1000 (regression OK)")
    return sale_id


# ============================================================================
# (B) ATTACH ADVANCES TESTS
# ============================================================================

def test_b1_create_customer():
    """Test B.1: Create customer for advance receipt tests"""
    print("\n" + "="*80)
    print("TEST B.1: Create customer for advance receipt tests")
    print("="*80)
    
    payload = {
        "name": "Advance Sale Customer",
        "phone": "9995550001",
        "address": "Test Address 123"
    }
    
    resp = requests.post(f"{API_BASE}/customers", json=payload, headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test B.1", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return None
    
    data = resp.json()
    customer_id = data.get("id")
    created_customer_ids.append(customer_id)
    
    log_test("Test B.1", "PASS", f"Customer created with id={customer_id}")
    return customer_id


def test_b2_create_advance_receipt(customer_id: str):
    """Test B.2: Create an ADVANCE receipt"""
    print("\n" + "="*80)
    print("TEST B.2: Create advance receipt")
    print("="*80)
    
    payload = {
        "customer_id": customer_id,
        "customer_name": "Advance Sale Customer",
        "customer_mobile": "9995550001",
        "amount": 300,
        "payment_mode": "cash",
        "source_type": "other"
    }
    
    resp = requests.post(f"{API_BASE}/receipts", json=payload, headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test B.2", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return None
    
    data = resp.json()
    receipt_id = data.get("id")
    created_receipt_ids.append(receipt_id)
    
    # Verify source_type is "other" (advance)
    if data.get("source_type") != "other":
        log_test("Test B.2", "FAIL", f"Expected source_type='other', got '{data.get('source_type')}'")
        return receipt_id
    
    log_test("Test B.2", "PASS", f"Advance receipt created with id={receipt_id}, source_type='other'")
    return receipt_id


def test_b3_verify_advance_in_list(customer_id: str, receipt_id: str):
    """Test B.3: GET /api/receipts/advances?customer_id=<id> → must include that receipt"""
    print("\n" + "="*80)
    print("TEST B.3: Verify advance receipt appears in advances list")
    print("="*80)
    
    resp = requests.get(f"{API_BASE}/receipts/advances?customer_id={customer_id}", 
                       headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test B.3", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return
    
    data = resp.json()
    
    # Verify response structure
    if "advances" not in data:
        log_test("Test B.3", "FAIL", f"Expected 'advances' key in response, got {data.keys()}")
        return
    
    advances = data.get("advances", [])
    advance_ids = [a.get("id") for a in advances]
    
    if receipt_id not in advance_ids:
        log_test("Test B.3", "FAIL", f"Receipt {receipt_id} not found in advances list. Found: {advance_ids}")
        return
    
    log_test("Test B.3", "PASS", 
             f"Receipt {receipt_id} found in advances list (count={data.get('count')}, total_amount={data.get('total_amount')})")


def test_b4_create_sale_with_attached_receipt(customer_id: str, receipt_id: str):
    """Test B.4: POST /api/sales with attach_receipt_ids → expect 200"""
    print("\n" + "="*80)
    print("TEST B.4: Create sale with attached advance receipt")
    print("="*80)
    
    payload = {
        "customer_id": customer_id,
        "customer_name": "Advance Sale Customer",
        "amount": 1000,
        "product": "Product with Advance",
        "attach_receipt_ids": [receipt_id]
    }
    
    resp = requests.post(f"{API_BASE}/sales", json=payload, headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test B.4", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return None
    
    data = resp.json()
    sale_id = data.get("id")
    created_sale_ids.append(sale_id)
    
    log_test("Test B.4", "PASS", f"Sale created with id={sale_id}, attached receipt {receipt_id}")
    return sale_id


def test_b5_verify_advance_removed_from_list(customer_id: str, receipt_id: str):
    """Test B.5: GET /api/receipts/advances?customer_id=<id> → the attached receipt must NO LONGER appear"""
    print("\n" + "="*80)
    print("TEST B.5: Verify attached receipt NO LONGER appears in advances list")
    print("="*80)
    
    resp = requests.get(f"{API_BASE}/receipts/advances?customer_id={customer_id}", 
                       headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test B.5", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return
    
    data = resp.json()
    advances = data.get("advances", [])
    advance_ids = [a.get("id") for a in advances]
    
    if receipt_id in advance_ids:
        log_test("Test B.5", "FAIL", 
                 f"Receipt {receipt_id} STILL appears in advances list after being attached to sale. "
                 f"It should have source_type='sale' now and be filtered out.")
        return
    
    log_test("Test B.5", "PASS", 
             f"Receipt {receipt_id} correctly removed from advances list (now linked to sale)")


# ============================================================================
# (C) SAFETY TEST
# ============================================================================

def test_c_attach_different_customer_receipt():
    """Test C: Attaching a receipt that belongs to a DIFFERENT customer must be silently ignored"""
    print("\n" + "="*80)
    print("TEST C: Safety - attach receipt from different customer (should be ignored)")
    print("="*80)
    
    # Create customer 1
    payload1 = {
        "name": "Customer One",
        "phone": "9995550011",
        "address": "Address 1"
    }
    resp1 = requests.post(f"{API_BASE}/customers", json=payload1, headers=auth_headers(), timeout=10)
    if resp1.status_code != 200:
        log_test("Test C (setup customer 1)", "FAIL", f"Failed to create customer 1: {resp1.status_code}")
        return
    customer1_id = resp1.json().get("id")
    created_customer_ids.append(customer1_id)
    
    # Create customer 2
    payload2 = {
        "name": "Customer Two",
        "phone": "9995550022",
        "address": "Address 2"
    }
    resp2 = requests.post(f"{API_BASE}/customers", json=payload2, headers=auth_headers(), timeout=10)
    if resp2.status_code != 200:
        log_test("Test C (setup customer 2)", "FAIL", f"Failed to create customer 2: {resp2.status_code}")
        return
    customer2_id = resp2.json().get("id")
    created_customer_ids.append(customer2_id)
    
    # Create advance receipt for customer 1
    receipt_payload = {
        "customer_id": customer1_id,
        "customer_name": "Customer One",
        "customer_mobile": "9995550011",
        "amount": 500,
        "payment_mode": "cash",
        "source_type": "other"
    }
    resp_receipt = requests.post(f"{API_BASE}/receipts", json=receipt_payload, headers=auth_headers(), timeout=10)
    if resp_receipt.status_code != 200:
        log_test("Test C (setup receipt)", "FAIL", f"Failed to create receipt: {resp_receipt.status_code}")
        return
    receipt_id = resp_receipt.json().get("id")
    created_receipt_ids.append(receipt_id)
    
    # Try to create sale for customer 2 with customer 1's receipt
    sale_payload = {
        "customer_id": customer2_id,
        "customer_name": "Customer Two",
        "amount": 2000,
        "product": "Product for Customer 2",
        "attach_receipt_ids": [receipt_id]  # This belongs to customer 1!
    }
    resp_sale = requests.post(f"{API_BASE}/sales", json=sale_payload, headers=auth_headers(), timeout=10)
    
    if resp_sale.status_code != 200:
        log_test("Test C", "FAIL", f"Expected 200 (sale created), got {resp_sale.status_code}: {resp_sale.text}")
        return
    
    sale_id = resp_sale.json().get("id")
    created_sale_ids.append(sale_id)
    
    # Verify the receipt is STILL an advance (not linked to the sale)
    resp_advances = requests.get(f"{API_BASE}/receipts/advances?customer_id={customer1_id}", 
                                headers=auth_headers(), timeout=10)
    if resp_advances.status_code != 200:
        log_test("Test C", "FAIL", f"Failed to get advances: {resp_advances.status_code}")
        return
    
    advances = resp_advances.json().get("advances", [])
    advance_ids = [a.get("id") for a in advances]
    
    if receipt_id not in advance_ids:
        log_test("Test C", "FAIL", 
                 f"Receipt {receipt_id} was incorrectly linked to customer 2's sale. "
                 f"It should remain an advance for customer 1.")
        return
    
    log_test("Test C", "PASS", 
             f"Sale created for customer 2, but customer 1's receipt {receipt_id} was correctly ignored "
             f"(still appears in customer 1's advances list)")


# ============================================================================
# (D) REGRESSION TESTS
# ============================================================================

def test_d1_get_sales_list(sale_id_with_profit: str):
    """Test D.1: GET /api/sales (scope=all and mine) still works and shows profit correctly"""
    print("\n" + "="*80)
    print("TEST D.1: Regression - GET /api/sales with profit field")
    print("="*80)
    
    # Test scope=all
    resp_all = requests.get(f"{API_BASE}/sales?scope=all", headers=auth_headers(), timeout=10)
    if resp_all.status_code != 200:
        log_test("Test D.1 (scope=all)", "FAIL", f"Expected 200, got {resp_all.status_code}: {resp_all.text}")
        return
    
    sales_all = resp_all.json()
    if not isinstance(sales_all, list):
        log_test("Test D.1 (scope=all)", "FAIL", f"Expected array response, got {type(sales_all)}")
        return
    
    # Find the sale with purchase_amount=600 and verify profit=400
    sale_found = None
    for sale in sales_all:
        if sale.get("id") == sale_id_with_profit:
            sale_found = sale
            break
    
    if not sale_found:
        log_test("Test D.1 (scope=all)", "FAIL", f"Sale {sale_id_with_profit} not found in sales list")
        return
    
    if sale_found.get("profit") != 400:
        log_test("Test D.1 (scope=all)", "FAIL", 
                 f"Expected profit=400 for sale {sale_id_with_profit}, got {sale_found.get('profit')}")
        return
    
    log_test("Test D.1 (scope=all)", "PASS", 
             f"GET /api/sales?scope=all returns {len(sales_all)} sales, "
             f"sale {sale_id_with_profit} shows profit=400 correctly")
    
    # Test scope=mine
    resp_mine = requests.get(f"{API_BASE}/sales?scope=mine", headers=auth_headers(), timeout=10)
    if resp_mine.status_code != 200:
        log_test("Test D.1 (scope=mine)", "FAIL", f"Expected 200, got {resp_mine.status_code}: {resp_mine.text}")
        return
    
    sales_mine = resp_mine.json()
    if not isinstance(sales_mine, list):
        log_test("Test D.1 (scope=mine)", "FAIL", f"Expected array response, got {type(sales_mine)}")
        return
    
    log_test("Test D.1 (scope=mine)", "PASS", f"GET /api/sales?scope=mine returns {len(sales_mine)} sales")


def test_d2_get_stats_sales_today():
    """Test D.2: GET /api/stats/sales-today still works"""
    print("\n" + "="*80)
    print("TEST D.2: Regression - GET /api/stats/sales-today")
    print("="*80)
    
    resp = requests.get(f"{API_BASE}/stats/sales-today", headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test D.2", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return
    
    data = resp.json()
    
    # Verify response structure
    required_keys = ["date", "count", "revenue", "profit"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        log_test("Test D.2", "FAIL", f"Missing keys in response: {missing_keys}")
        return
    
    log_test("Test D.2", "PASS", 
             f"GET /api/stats/sales-today returns correct structure "
             f"(date={data.get('date')}, count={data.get('count')}, revenue={data.get('revenue')}, profit={data.get('profit')})")


def test_d3_get_deliveries():
    """Test D.3: GET /api/deliveries still works (unaffected)"""
    print("\n" + "="*80)
    print("TEST D.3: Regression - GET /api/deliveries")
    print("="*80)
    
    resp = requests.get(f"{API_BASE}/deliveries?status=all", headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test D.3", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return
    
    data = resp.json()
    
    # Verify response structure
    required_keys = ["date", "count", "deliveries"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        log_test("Test D.3", "FAIL", f"Missing keys in response: {missing_keys}")
        return
    
    log_test("Test D.3", "PASS", 
             f"GET /api/deliveries returns correct structure (count={data.get('count')})")


def test_d4_get_receipts_advances():
    """Test D.4: GET /api/receipts/advances still works (unaffected)"""
    print("\n" + "="*80)
    print("TEST D.4: Regression - GET /api/receipts/advances")
    print("="*80)
    
    # Use a test phone number
    resp = requests.get(f"{API_BASE}/receipts/advances?phone=9999999999", headers=auth_headers(), timeout=10)
    
    if resp.status_code != 200:
        log_test("Test D.4", "FAIL", f"Expected 200, got {resp.status_code}: {resp.text}")
        return
    
    data = resp.json()
    
    # Verify response structure
    required_keys = ["advances", "count", "total_amount"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        log_test("Test D.4", "FAIL", f"Missing keys in response: {missing_keys}")
        return
    
    log_test("Test D.4", "PASS", 
             f"GET /api/receipts/advances returns correct structure (count={data.get('count')})")


# ============================================================================
# CLEANUP
# ============================================================================

def cleanup():
    """Delete all test data"""
    print("\n" + "="*80)
    print("CLEANUP: Deleting test data")
    print("="*80)
    
    deleted_sales = 0
    deleted_receipts = 0
    deleted_customers = 0
    failed = 0
    
    # Delete sales
    for sale_id in created_sale_ids:
        try:
            resp = requests.delete(f"{API_BASE}/sales/{sale_id}", headers=auth_headers(), timeout=10)
            if resp.status_code in [200, 204]:
                deleted_sales += 1
                print(f"   ✅ Deleted sale {sale_id}")
            else:
                failed += 1
                print(f"   ⚠️  Failed to delete sale {sale_id}: {resp.status_code}")
        except Exception as e:
            failed += 1
            print(f"   ⚠️  Error deleting sale {sale_id}: {e}")
    
    # Delete receipts
    for receipt_id in created_receipt_ids:
        try:
            resp = requests.delete(f"{API_BASE}/receipts/{receipt_id}", headers=auth_headers(), timeout=10)
            if resp.status_code in [200, 204]:
                deleted_receipts += 1
                print(f"   ✅ Deleted receipt {receipt_id}")
            else:
                failed += 1
                print(f"   ⚠️  Failed to delete receipt {receipt_id}: {resp.status_code}")
        except Exception as e:
            failed += 1
            print(f"   ⚠️  Error deleting receipt {receipt_id}: {e}")
    
    # Delete customers
    for customer_id in created_customer_ids:
        try:
            resp = requests.delete(f"{API_BASE}/customers/{customer_id}", headers=auth_headers(), timeout=10)
            if resp.status_code in [200, 204]:
                deleted_customers += 1
                print(f"   ✅ Deleted customer {customer_id}")
            else:
                failed += 1
                print(f"   ⚠️  Failed to delete customer {customer_id}: {resp.status_code}")
        except Exception as e:
            failed += 1
            print(f"   ⚠️  Error deleting customer {customer_id}: {e}")
    
    print(f"\nCleanup complete: {deleted_sales} sales, {deleted_receipts} receipts, "
          f"{deleted_customers} customers deleted, {failed} failed")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests"""
    global access_token
    
    print("\n" + "="*80)
    print("SALE CREATION WITH PURCHASE_AMOUNT & ATTACH_RECEIPT_IDS TESTS")
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
        
        # ========== (A) PURCHASE COST TESTS ==========
        print("\n" + "="*80)
        print("SECTION A: PURCHASE COST TESTS")
        print("="*80)
        
        sale_id_with_profit = test_a1_sale_with_purchase_amount()
        test_a2_sale_with_negative_purchase_amount()
        test_a3_sale_without_purchase_amount()
        
        # ========== (B) ATTACH ADVANCES TESTS ==========
        print("\n" + "="*80)
        print("SECTION B: ATTACH ADVANCES TESTS")
        print("="*80)
        
        customer_id = test_b1_create_customer()
        if customer_id:
            receipt_id = test_b2_create_advance_receipt(customer_id)
            if receipt_id:
                test_b3_verify_advance_in_list(customer_id, receipt_id)
                sale_id = test_b4_create_sale_with_attached_receipt(customer_id, receipt_id)
                if sale_id:
                    test_b5_verify_advance_removed_from_list(customer_id, receipt_id)
        
        # ========== (C) SAFETY TEST ==========
        print("\n" + "="*80)
        print("SECTION C: SAFETY TEST")
        print("="*80)
        
        test_c_attach_different_customer_receipt()
        
        # ========== (D) REGRESSION TESTS ==========
        print("\n" + "="*80)
        print("SECTION D: REGRESSION TESTS")
        print("="*80)
        
        if sale_id_with_profit:
            test_d1_get_sales_list(sale_id_with_profit)
        test_d2_get_stats_sales_today()
        test_d3_get_deliveries()
        test_d4_get_receipts_advances()
        
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
        if created_customer_ids or created_receipt_ids or created_sale_ids:
            print("\nAttempting cleanup after error...")
            cleanup()


if __name__ == "__main__":
    main()
