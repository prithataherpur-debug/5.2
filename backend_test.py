#!/usr/bin/env python3
"""
Backend test for partial advance allocation feature.
Tests the new advance_allocations field on sales & invoices.
"""
import requests
import json
from typing import Optional

# Configuration
BASE_URL = "https://6661bdad-da1a-401e-b57e-0be08928ca8f.preview.emergentagent.com/api"
ADMIN_USER = "admin"
ADMIN_PASS = "Admin@2026"
EMP_USER = "emp1"
EMP_PASS = "Emp@2026"

# Test data tracking for cleanup
test_customers = []
test_receipts = []
test_sales = []
test_invoices = []

def login(username: str, password: str) -> str:
    """Login and return access token."""
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.status_code} {resp.text}")
    return resp.json()["access_token"]

def headers(token: str) -> dict:
    """Return authorization headers."""
    return {"Authorization": f"Bearer {token}"}

def cleanup_all(token: str):
    """Clean up all test data."""
    print("\n🧹 CLEANUP: Removing test data...")
    
    # Delete sales
    for sale_id in test_sales:
        try:
            resp = requests.delete(f"{BASE_URL}/sales/{sale_id}", headers=headers(token))
            if resp.status_code == 200:
                print(f"  ✓ Deleted sale {sale_id}")
        except Exception as e:
            print(f"  ⚠ Failed to delete sale {sale_id}: {e}")
    
    # Delete invoices
    for inv_id in test_invoices:
        try:
            resp = requests.delete(f"{BASE_URL}/invoices/{inv_id}", headers=headers(token))
            if resp.status_code == 200:
                print(f"  ✓ Deleted invoice {inv_id}")
        except Exception as e:
            print(f"  ⚠ Failed to delete invoice {inv_id}: {e}")
    
    # Delete receipts
    for receipt_id in test_receipts:
        try:
            resp = requests.delete(f"{BASE_URL}/receipts/{receipt_id}", headers=headers(token))
            if resp.status_code == 200:
                print(f"  ✓ Deleted receipt {receipt_id}")
        except Exception as e:
            print(f"  ⚠ Failed to delete receipt {receipt_id}: {e}")
    
    # Delete customers
    for cust_id in test_customers:
        try:
            resp = requests.delete(f"{BASE_URL}/customers/{cust_id}", headers=headers(token))
            if resp.status_code == 200:
                print(f"  ✓ Deleted customer {cust_id}")
        except Exception as e:
            print(f"  ⚠ Failed to delete customer {cust_id}: {e}")
    
    print("✅ Cleanup complete\n")

def test_scenario_1_setup(token: str):
    """SCENARIO 1: SETUP - Create customer and advance receipt."""
    print("\n📋 SCENARIO 1: SETUP - Create customer and advance receipt")
    
    # Create customer
    cust_resp = requests.post(
        f"{BASE_URL}/customers",
        headers=headers(token),
        json={"name": "Alloc Test", "phone": "9994440001", "address": "x"}
    )
    if cust_resp.status_code != 200:
        print(f"❌ FAIL: Customer creation failed: {cust_resp.status_code} {cust_resp.text}")
        return None, None
    
    customer = cust_resp.json()
    customer_id = customer["id"]
    test_customers.append(customer_id)
    print(f"  ✓ Created customer: {customer_id} (name: {customer['name']}, phone: {customer['phone']})")
    
    # Create advance receipt
    receipt_resp = requests.post(
        f"{BASE_URL}/receipts",
        headers=headers(token),
        json={
            "customer_id": customer_id,
            "customer_name": "Alloc Test",
            "customer_mobile": "9994440001",
            "amount": 1000,
            "payment_mode": "cash",
            "source_type": "other"
        }
    )
    if receipt_resp.status_code != 200:
        print(f"❌ FAIL: Receipt creation failed: {receipt_resp.status_code} {receipt_resp.text}")
        return customer_id, None
    
    receipt = receipt_resp.json()
    receipt_id = receipt["id"]
    test_receipts.append(receipt_id)
    print(f"  ✓ Created advance receipt: {receipt_id} (amount: {receipt['amount']}, source_type: {receipt.get('source_type')})")
    
    print("✅ SCENARIO 1: PASS - Setup complete")
    return customer_id, receipt_id

def test_scenario_2_verify_available(token: str, customer_id: str, receipt_id: str):
    """SCENARIO 2: VERIFY AVAILABLE - Check advances list shows receipt with allocated=0, remaining=1000."""
    print("\n📋 SCENARIO 2: VERIFY AVAILABLE - Check advances list")
    
    resp = requests.get(
        f"{BASE_URL}/receipts/advances",
        headers=headers(token),
        params={"customer_id": customer_id}
    )
    if resp.status_code != 200:
        print(f"❌ FAIL: GET /receipts/advances failed: {resp.status_code} {resp.text}")
        return False
    
    data = resp.json()
    print(f"  Response: count={data.get('count')}, total_amount={data.get('total_amount')}")
    
    # Verify structure
    if "advances" not in data or "count" not in data or "total_amount" not in data:
        print(f"❌ FAIL: Missing required fields in response")
        return False
    
    # Find our receipt
    receipt_found = None
    for adv in data["advances"]:
        if adv["id"] == receipt_id:
            receipt_found = adv
            break
    
    if not receipt_found:
        print(f"❌ FAIL: Receipt {receipt_id} not found in advances list")
        return False
    
    # Verify allocated=0, remaining=1000
    allocated = receipt_found.get("allocated", -1)
    remaining = receipt_found.get("remaining", -1)
    
    print(f"  Receipt found: allocated={allocated}, remaining={remaining}")
    
    if allocated != 0:
        print(f"❌ FAIL: Expected allocated=0, got {allocated}")
        return False
    
    if remaining != 1000:
        print(f"❌ FAIL: Expected remaining=1000, got {remaining}")
        return False
    
    if data["count"] < 1:
        print(f"❌ FAIL: Expected count >= 1, got {data['count']}")
        return False
    
    if data["total_amount"] < 1000:
        print(f"❌ FAIL: Expected total_amount >= 1000, got {data['total_amount']}")
        return False
    
    print("✅ SCENARIO 2: PASS - Advances list correct (allocated=0, remaining=1000)")
    return True

def test_scenario_3_partial_on_sale(token: str, customer_id: str, receipt_id: str):
    """SCENARIO 3: PARTIAL ON SALE - Apply 400 to a sale, verify linked_receipts."""
    print("\n📋 SCENARIO 3: PARTIAL ON SALE - Apply 400 to a sale")
    
    # Create sale with partial advance allocation
    sale_resp = requests.post(
        f"{BASE_URL}/sales",
        headers=headers(token),
        json={
            "customer_id": customer_id,
            "customer_name": "Alloc Test",
            "amount": 2000,
            "advance_allocations": [{"receipt_id": receipt_id, "amount": 400}]
        }
    )
    if sale_resp.status_code != 200:
        print(f"❌ FAIL: Sale creation failed: {sale_resp.status_code} {sale_resp.text}")
        return None
    
    sale = sale_resp.json()
    sale_id = sale["id"]
    test_sales.append(sale_id)
    print(f"  ✓ Created sale: {sale_id} (amount: {sale['amount']})")
    
    # Get sales list to verify linked_receipts
    sales_resp = requests.get(
        f"{BASE_URL}/sales",
        headers=headers(token),
        params={"scope": "all"}
    )
    if sales_resp.status_code != 200:
        print(f"❌ FAIL: GET /sales failed: {sales_resp.status_code} {sales_resp.text}")
        return sale_id
    
    sales = sales_resp.json()
    sale_found = None
    for s in sales:
        if s["id"] == sale_id:
            sale_found = s
            break
    
    if not sale_found:
        print(f"❌ FAIL: Sale {sale_id} not found in sales list")
        return sale_id
    
    # Verify linked_receipts contains advance entry
    linked_receipts = sale_found.get("linked_receipts", [])
    print(f"  Sale has {len(linked_receipts)} linked_receipts")
    
    advance_found = None
    for lr in linked_receipts:
        if lr.get("is_advance") and lr.get("source_type") == "advance":
            advance_found = lr
            break
    
    if not advance_found:
        print(f"❌ FAIL: No advance entry found in linked_receipts")
        print(f"  linked_receipts: {json.dumps(linked_receipts, indent=2)}")
        return sale_id
    
    # Verify amount=400
    if advance_found.get("amount") != 400:
        print(f"❌ FAIL: Expected advance amount=400, got {advance_found.get('amount')}")
        return sale_id
    
    # Verify receipt_no is set
    if not advance_found.get("receipt_no"):
        print(f"❌ FAIL: receipt_no not set on advance entry")
        return sale_id
    
    print(f"  ✓ Advance entry found: amount={advance_found['amount']}, receipt_no={advance_found['receipt_no']}, is_advance={advance_found['is_advance']}")
    print("✅ SCENARIO 3: PASS - Partial advance applied to sale correctly")
    return sale_id

def test_scenario_4_remaining_still_listed(token: str, customer_id: str, receipt_id: str):
    """SCENARIO 4: REMAINING STILL LISTED - Check advances shows allocated=400, remaining=600."""
    print("\n📋 SCENARIO 4: REMAINING STILL LISTED - Check advances after partial use")
    
    resp = requests.get(
        f"{BASE_URL}/receipts/advances",
        headers=headers(token),
        params={"customer_id": customer_id}
    )
    if resp.status_code != 200:
        print(f"❌ FAIL: GET /receipts/advances failed: {resp.status_code} {resp.text}")
        return False
    
    data = resp.json()
    
    # Find our receipt
    receipt_found = None
    for adv in data["advances"]:
        if adv["id"] == receipt_id:
            receipt_found = adv
            break
    
    if not receipt_found:
        print(f"❌ FAIL: Receipt {receipt_id} not found in advances list (should still be there with remaining=600)")
        return False
    
    # Verify allocated=400, remaining=600
    allocated = receipt_found.get("allocated", -1)
    remaining = receipt_found.get("remaining", -1)
    
    print(f"  Receipt found: allocated={allocated}, remaining={remaining}")
    
    if allocated != 400:
        print(f"❌ FAIL: Expected allocated=400, got {allocated}")
        return False
    
    if remaining != 600:
        print(f"❌ FAIL: Expected remaining=600, got {remaining}")
        return False
    
    # Verify total_amount reflects remaining (not original amount)
    if data["total_amount"] < 600:
        print(f"❌ FAIL: Expected total_amount >= 600, got {data['total_amount']}")
        return False
    
    print("✅ SCENARIO 4: PASS - Receipt still listed with allocated=400, remaining=600")
    return True

def test_scenario_5_rest_on_invoice(token: str, customer_id: str, receipt_id: str):
    """SCENARIO 5: REST ON INVOICE - Apply remaining 600 to invoice."""
    print("\n📋 SCENARIO 5: REST ON INVOICE - Apply remaining 600 to invoice")
    
    # Create invoice with remaining advance allocation
    inv_resp = requests.post(
        f"{BASE_URL}/invoices",
        headers=headers(token),
        json={
            "customer_id": customer_id,
            "customer_name": "Alloc Test",
            "customer_mobile": "9994440001",
            "items": [{"name": "Item", "qty": 1, "unit_price": 5000, "unit_cost": 0}],
            "advance_allocations": [{"receipt_id": receipt_id, "amount": 600}]
        }
    )
    if inv_resp.status_code != 200:
        print(f"❌ FAIL: Invoice creation failed: {inv_resp.status_code} {inv_resp.text}")
        return None
    
    invoice = inv_resp.json()
    invoice_id = invoice["id"]
    invoice_no = invoice.get("invoice_no")
    test_invoices.append(invoice_id)
    print(f"  ✓ Created invoice: {invoice_id} (invoice_no: {invoice_no}, total: {invoice.get('total')})")
    
    # Get invoices list to verify linked_receipts
    inv_list_resp = requests.get(
        f"{BASE_URL}/invoices",
        headers=headers(token)
    )
    if inv_list_resp.status_code != 200:
        print(f"❌ FAIL: GET /invoices failed: {inv_list_resp.status_code} {inv_list_resp.text}")
        return invoice_id
    
    invoices = inv_list_resp.json()
    invoice_found = None
    for inv in invoices:
        if inv["id"] == invoice_id:
            invoice_found = inv
            break
    
    if not invoice_found:
        print(f"❌ FAIL: Invoice {invoice_id} not found in invoices list")
        return invoice_id
    
    # Verify linked_receipts contains advance entry
    linked_receipts = invoice_found.get("linked_receipts", [])
    print(f"  Invoice has {len(linked_receipts)} linked_receipts")
    
    advance_found = None
    for lr in linked_receipts:
        if lr.get("is_advance") and lr.get("source_type") == "advance":
            advance_found = lr
            break
    
    if not advance_found:
        print(f"❌ FAIL: No advance entry found in invoice linked_receipts")
        print(f"  linked_receipts: {json.dumps(linked_receipts, indent=2)}")
        return invoice_id
    
    # Verify amount=600
    if advance_found.get("amount") != 600:
        print(f"❌ FAIL: Expected advance amount=600, got {advance_found.get('amount')}")
        return invoice_id
    
    print(f"  ✓ Advance entry found: amount={advance_found['amount']}, is_advance={advance_found['is_advance']}")
    print("✅ SCENARIO 5: PASS - Remaining 600 applied to invoice correctly")
    return invoice_id

def test_scenario_6_fully_consumed(token: str, customer_id: str, receipt_id: str):
    """SCENARIO 6: FULLY CONSUMED - Check receipt no longer appears in advances."""
    print("\n📋 SCENARIO 6: FULLY CONSUMED - Check receipt no longer in advances list")
    
    resp = requests.get(
        f"{BASE_URL}/receipts/advances",
        headers=headers(token),
        params={"customer_id": customer_id}
    )
    if resp.status_code != 200:
        print(f"❌ FAIL: GET /receipts/advances failed: {resp.status_code} {resp.text}")
        return False
    
    data = resp.json()
    
    # Verify receipt is NOT in the list
    receipt_found = None
    for adv in data["advances"]:
        if adv["id"] == receipt_id:
            receipt_found = adv
            break
    
    if receipt_found:
        print(f"❌ FAIL: Receipt {receipt_id} still appears in advances list (should be gone, remaining=0)")
        print(f"  Receipt data: allocated={receipt_found.get('allocated')}, remaining={receipt_found.get('remaining')}")
        return False
    
    print(f"  ✓ Receipt {receipt_id} correctly removed from advances list (fully consumed)")
    print(f"  Current advances count: {data['count']}, total_amount: {data['total_amount']}")
    print("✅ SCENARIO 6: PASS - Fully consumed receipt no longer listed")
    return True

def test_scenario_7_over_allocation_cap(token: str):
    """SCENARIO 7: OVER-ALLOCATION CAP - Test capping at available amount."""
    print("\n📋 SCENARIO 7: OVER-ALLOCATION CAP - Test amount capping")
    
    # Create a fresh customer and advance
    cust_resp = requests.post(
        f"{BASE_URL}/customers",
        headers=headers(token),
        json={"name": "Cap Test", "phone": "9994440002", "address": "x"}
    )
    if cust_resp.status_code != 200:
        print(f"❌ FAIL: Customer creation failed: {cust_resp.status_code} {cust_resp.text}")
        return False
    
    customer = cust_resp.json()
    customer_id = customer["id"]
    test_customers.append(customer_id)
    
    # Create advance with amount=500
    receipt_resp = requests.post(
        f"{BASE_URL}/receipts",
        headers=headers(token),
        json={
            "customer_id": customer_id,
            "customer_name": "Cap Test",
            "customer_mobile": "9994440002",
            "amount": 500,
            "payment_mode": "cash",
            "source_type": "other"
        }
    )
    if receipt_resp.status_code != 200:
        print(f"❌ FAIL: Receipt creation failed: {receipt_resp.status_code} {receipt_resp.text}")
        return False
    
    receipt = receipt_resp.json()
    receipt_id = receipt["id"]
    test_receipts.append(receipt_id)
    print(f"  ✓ Created advance: {receipt_id} (amount: 500)")
    
    # Try to apply 900 (more than available)
    sale_resp = requests.post(
        f"{BASE_URL}/sales",
        headers=headers(token),
        json={
            "customer_id": customer_id,
            "customer_name": "Cap Test",
            "amount": 2000,
            "advance_allocations": [{"receipt_id": receipt_id, "amount": 900}]
        }
    )
    if sale_resp.status_code != 200:
        print(f"❌ FAIL: Sale creation failed: {sale_resp.status_code} {sale_resp.text}")
        return False
    
    sale = sale_resp.json()
    sale_id = sale["id"]
    test_sales.append(sale_id)
    print(f"  ✓ Created sale: {sale_id} (requested advance: 900)")
    
    # Get sale to verify linked advance amount is capped at 500
    sales_resp = requests.get(
        f"{BASE_URL}/sales",
        headers=headers(token),
        params={"scope": "all"}
    )
    if sales_resp.status_code != 200:
        print(f"❌ FAIL: GET /sales failed: {sales_resp.status_code} {sales_resp.text}")
        return False
    
    sales = sales_resp.json()
    sale_found = None
    for s in sales:
        if s["id"] == sale_id:
            sale_found = s
            break
    
    if not sale_found:
        print(f"❌ FAIL: Sale {sale_id} not found")
        return False
    
    # Find advance in linked_receipts
    linked_receipts = sale_found.get("linked_receipts", [])
    advance_found = None
    for lr in linked_receipts:
        if lr.get("is_advance"):
            advance_found = lr
            break
    
    if not advance_found:
        print(f"❌ FAIL: No advance entry found in linked_receipts")
        return False
    
    # Verify amount is capped at 500 (not 900)
    if advance_found.get("amount") != 500:
        print(f"❌ FAIL: Expected advance amount=500 (capped), got {advance_found.get('amount')}")
        return False
    
    print(f"  ✓ Advance amount correctly capped at 500 (requested 900)")
    
    # Verify receipt is fully consumed
    adv_resp = requests.get(
        f"{BASE_URL}/receipts/advances",
        headers=headers(token),
        params={"customer_id": customer_id}
    )
    if adv_resp.status_code != 200:
        print(f"❌ FAIL: GET /receipts/advances failed: {adv_resp.status_code} {adv_resp.text}")
        return False
    
    adv_data = adv_resp.json()
    receipt_found = None
    for adv in adv_data["advances"]:
        if adv["id"] == receipt_id:
            receipt_found = adv
            break
    
    if receipt_found:
        print(f"❌ FAIL: Receipt still in advances list (should be gone, remaining=0)")
        print(f"  Receipt: allocated={receipt_found.get('allocated')}, remaining={receipt_found.get('remaining')}")
        return False
    
    print(f"  ✓ Receipt correctly removed from advances (remaining=0)")
    print("✅ SCENARIO 7: PASS - Over-allocation correctly capped at available amount")
    return True

def test_scenario_8_cross_customer_safety(token: str):
    """SCENARIO 8: CROSS-CUSTOMER SAFETY - Test mismatched customer receipts are ignored."""
    print("\n📋 SCENARIO 8: CROSS-CUSTOMER SAFETY - Test cross-customer receipt rejection")
    
    # Create customer 1
    cust1_resp = requests.post(
        f"{BASE_URL}/customers",
        headers=headers(token),
        json={"name": "Customer 1", "phone": "9994440003", "address": "x"}
    )
    if cust1_resp.status_code != 200:
        print(f"❌ FAIL: Customer 1 creation failed: {cust1_resp.status_code} {cust1_resp.text}")
        return False
    
    customer1 = cust1_resp.json()
    customer1_id = customer1["id"]
    test_customers.append(customer1_id)
    
    # Create customer 2
    cust2_resp = requests.post(
        f"{BASE_URL}/customers",
        headers=headers(token),
        json={"name": "Customer 2", "phone": "9994440004", "address": "x"}
    )
    if cust2_resp.status_code != 200:
        print(f"❌ FAIL: Customer 2 creation failed: {cust2_resp.status_code} {cust2_resp.text}")
        return False
    
    customer2 = cust2_resp.json()
    customer2_id = customer2["id"]
    test_customers.append(customer2_id)
    
    print(f"  ✓ Created customer 1: {customer1_id}")
    print(f"  ✓ Created customer 2: {customer2_id}")
    
    # Create advance for customer 2
    receipt_resp = requests.post(
        f"{BASE_URL}/receipts",
        headers=headers(token),
        json={
            "customer_id": customer2_id,
            "customer_name": "Customer 2",
            "customer_mobile": "9994440004",
            "amount": 800,
            "payment_mode": "cash",
            "source_type": "other"
        }
    )
    if receipt_resp.status_code != 200:
        print(f"❌ FAIL: Receipt creation failed: {receipt_resp.status_code} {receipt_resp.text}")
        return False
    
    receipt = receipt_resp.json()
    receipt_id = receipt["id"]
    test_receipts.append(receipt_id)
    print(f"  ✓ Created advance for customer 2: {receipt_id} (amount: 800)")
    
    # Try to create sale for customer 1 with customer 2's receipt
    sale_resp = requests.post(
        f"{BASE_URL}/sales",
        headers=headers(token),
        json={
            "customer_id": customer1_id,
            "customer_name": "Customer 1",
            "amount": 1500,
            "advance_allocations": [{"receipt_id": receipt_id, "amount": 500}]
        }
    )
    if sale_resp.status_code != 200:
        print(f"❌ FAIL: Sale creation failed: {sale_resp.status_code} {sale_resp.text}")
        return False
    
    sale = sale_resp.json()
    sale_id = sale["id"]
    test_sales.append(sale_id)
    print(f"  ✓ Created sale for customer 1: {sale_id} (with customer 2's receipt)")
    
    # Verify sale has NO advance linked
    sales_resp = requests.get(
        f"{BASE_URL}/sales",
        headers=headers(token),
        params={"scope": "all"}
    )
    if sales_resp.status_code != 200:
        print(f"❌ FAIL: GET /sales failed: {sales_resp.status_code} {sales_resp.text}")
        return False
    
    sales = sales_resp.json()
    sale_found = None
    for s in sales:
        if s["id"] == sale_id:
            sale_found = s
            break
    
    if not sale_found:
        print(f"❌ FAIL: Sale {sale_id} not found")
        return False
    
    # Verify NO advance in linked_receipts
    linked_receipts = sale_found.get("linked_receipts", [])
    advance_found = None
    for lr in linked_receipts:
        if lr.get("is_advance"):
            advance_found = lr
            break
    
    if advance_found:
        print(f"❌ FAIL: Mismatched receipt was incorrectly linked to sale")
        print(f"  Advance entry: {json.dumps(advance_found, indent=2)}")
        return False
    
    print(f"  ✓ Sale has no advance linked (mismatched receipt correctly ignored)")
    
    # Verify customer 2's receipt is still fully available
    adv_resp = requests.get(
        f"{BASE_URL}/receipts/advances",
        headers=headers(token),
        params={"customer_id": customer2_id}
    )
    if adv_resp.status_code != 200:
        print(f"❌ FAIL: GET /receipts/advances failed: {adv_resp.status_code} {adv_resp.text}")
        return False
    
    adv_data = adv_resp.json()
    receipt_found = None
    for adv in adv_data["advances"]:
        if adv["id"] == receipt_id:
            receipt_found = adv
            break
    
    if not receipt_found:
        print(f"❌ FAIL: Customer 2's receipt not found in advances (should still be there)")
        return False
    
    if receipt_found.get("remaining") != 800:
        print(f"❌ FAIL: Expected remaining=800, got {receipt_found.get('remaining')}")
        return False
    
    print(f"  ✓ Customer 2's receipt still fully available (remaining=800)")
    print("✅ SCENARIO 8: PASS - Cross-customer receipts correctly ignored")
    return True

def test_scenario_9_legacy_attach_receipt_ids(token: str):
    """SCENARIO 9: LEGACY attach_receipt_ids REGRESSION - Test old field still works."""
    print("\n📋 SCENARIO 9: LEGACY attach_receipt_ids - Test backward compatibility")
    
    # Create customer and advance
    cust_resp = requests.post(
        f"{BASE_URL}/customers",
        headers=headers(token),
        json={"name": "Legacy Test", "phone": "9994440005", "address": "x"}
    )
    if cust_resp.status_code != 200:
        print(f"❌ FAIL: Customer creation failed: {cust_resp.status_code} {cust_resp.text}")
        return False
    
    customer = cust_resp.json()
    customer_id = customer["id"]
    test_customers.append(customer_id)
    
    receipt_resp = requests.post(
        f"{BASE_URL}/receipts",
        headers=headers(token),
        json={
            "customer_id": customer_id,
            "customer_name": "Legacy Test",
            "customer_mobile": "9994440005",
            "amount": 300,
            "payment_mode": "cash",
            "source_type": "other"
        }
    )
    if receipt_resp.status_code != 200:
        print(f"❌ FAIL: Receipt creation failed: {receipt_resp.status_code} {receipt_resp.text}")
        return False
    
    receipt = receipt_resp.json()
    receipt_id = receipt["id"]
    test_receipts.append(receipt_id)
    print(f"  ✓ Created advance: {receipt_id} (amount: 300)")
    
    # Create sale with legacy attach_receipt_ids (no advance_allocations)
    sale_resp = requests.post(
        f"{BASE_URL}/sales",
        headers=headers(token),
        json={
            "customer_id": customer_id,
            "customer_name": "Legacy Test",
            "amount": 1000,
            "attach_receipt_ids": [receipt_id]
        }
    )
    if sale_resp.status_code != 200:
        print(f"❌ FAIL: Sale creation failed: {sale_resp.status_code} {sale_resp.text}")
        return False
    
    sale = sale_resp.json()
    sale_id = sale["id"]
    test_sales.append(sale_id)
    print(f"  ✓ Created sale with legacy attach_receipt_ids: {sale_id}")
    
    # Verify full 300 is applied
    sales_resp = requests.get(
        f"{BASE_URL}/sales",
        headers=headers(token),
        params={"scope": "all"}
    )
    if sales_resp.status_code != 200:
        print(f"❌ FAIL: GET /sales failed: {sales_resp.status_code} {sales_resp.text}")
        return False
    
    sales = sales_resp.json()
    sale_found = None
    for s in sales:
        if s["id"] == sale_id:
            sale_found = s
            break
    
    if not sale_found:
        print(f"❌ FAIL: Sale {sale_id} not found")
        return False
    
    # Find advance in linked_receipts
    linked_receipts = sale_found.get("linked_receipts", [])
    advance_found = None
    for lr in linked_receipts:
        if lr.get("is_advance"):
            advance_found = lr
            break
    
    if not advance_found:
        print(f"❌ FAIL: No advance entry found in linked_receipts")
        return False
    
    # Verify amount=300 (full amount)
    if advance_found.get("amount") != 300:
        print(f"❌ FAIL: Expected advance amount=300 (full), got {advance_found.get('amount')}")
        return False
    
    print(f"  ✓ Full 300 applied via legacy attach_receipt_ids")
    
    # Verify receipt is gone from advances
    adv_resp = requests.get(
        f"{BASE_URL}/receipts/advances",
        headers=headers(token),
        params={"customer_id": customer_id}
    )
    if adv_resp.status_code != 200:
        print(f"❌ FAIL: GET /receipts/advances failed: {adv_resp.status_code} {adv_resp.text}")
        return False
    
    adv_data = adv_resp.json()
    receipt_found = None
    for adv in adv_data["advances"]:
        if adv["id"] == receipt_id:
            receipt_found = adv
            break
    
    if receipt_found:
        print(f"❌ FAIL: Receipt still in advances (should be gone, remaining=0)")
        return False
    
    print(f"  ✓ Receipt correctly removed from advances (remaining=0)")
    print("✅ SCENARIO 9: PASS - Legacy attach_receipt_ids works correctly")
    return True

def test_scenario_10_regression(token: str):
    """SCENARIO 10: REGRESSION - Check other endpoints still work."""
    print("\n📋 SCENARIO 10: REGRESSION - Check other endpoints")
    
    all_pass = True
    
    # Test GET /sales
    resp = requests.get(f"{BASE_URL}/sales", headers=headers(token), params={"scope": "all"})
    if resp.status_code != 200:
        print(f"  ❌ GET /sales failed: {resp.status_code}")
        all_pass = False
    else:
        sales = resp.json()
        if not isinstance(sales, list):
            print(f"  ❌ GET /sales returned non-list: {type(sales)}")
            all_pass = False
        else:
            print(f"  ✓ GET /sales: 200 OK (returned {len(sales)} sales)")
    
    # Test GET /invoices
    resp = requests.get(f"{BASE_URL}/invoices", headers=headers(token))
    if resp.status_code != 200:
        print(f"  ❌ GET /invoices failed: {resp.status_code}")
        all_pass = False
    else:
        invoices = resp.json()
        if not isinstance(invoices, list):
            print(f"  ❌ GET /invoices returned non-list: {type(invoices)}")
            all_pass = False
        else:
            print(f"  ✓ GET /invoices: 200 OK (returned {len(invoices)} invoices)")
    
    # Test GET /stats/sales-today
    resp = requests.get(f"{BASE_URL}/stats/sales-today", headers=headers(token))
    if resp.status_code != 200:
        print(f"  ❌ GET /stats/sales-today failed: {resp.status_code}")
        all_pass = False
    else:
        data = resp.json()
        if "date" not in data or "count" not in data:
            print(f"  ❌ GET /stats/sales-today missing required fields")
            all_pass = False
        else:
            print(f"  ✓ GET /stats/sales-today: 200 OK (date={data['date']}, count={data['count']})")
    
    # Test GET /deliveries
    resp = requests.get(f"{BASE_URL}/deliveries", headers=headers(token))
    if resp.status_code != 200:
        print(f"  ❌ GET /deliveries failed: {resp.status_code}")
        all_pass = False
    else:
        data = resp.json()
        if "deliveries" not in data:
            print(f"  ❌ GET /deliveries missing 'deliveries' field")
            all_pass = False
        else:
            print(f"  ✓ GET /deliveries: 200 OK (returned {len(data['deliveries'])} deliveries)")
    
    # Create a normal sale without advances
    sale_resp = requests.post(
        f"{BASE_URL}/sales",
        headers=headers(token),
        json={
            "customer_name": "Normal Sale",
            "amount": 500
        }
    )
    if sale_resp.status_code != 200:
        print(f"  ❌ Normal sale creation failed: {sale_resp.status_code}")
        all_pass = False
    else:
        sale = sale_resp.json()
        test_sales.append(sale["id"])
        linked_receipts = sale.get("linked_receipts")
        if not isinstance(linked_receipts, list):
            print(f"  ❌ Normal sale linked_receipts is not a list: {type(linked_receipts)}")
            all_pass = False
        else:
            print(f"  ✓ Normal sale created: linked_receipts is array (len={len(linked_receipts)})")
    
    if all_pass:
        print("✅ SCENARIO 10: PASS - All regression checks passed")
    else:
        print("❌ SCENARIO 10: FAIL - Some regression checks failed")
    
    return all_pass

def main():
    """Run all test scenarios."""
    print("=" * 80)
    print("PARTIAL ADVANCE ALLOCATION BACKEND TEST")
    print("=" * 80)
    
    try:
        # Login
        print("\n🔐 Logging in as admin...")
        token = login(ADMIN_USER, ADMIN_PASS)
        print(f"✓ Logged in successfully")
        
        # Track results
        results = {}
        
        # SCENARIO 1: Setup
        customer_id, receipt_id = test_scenario_1_setup(token)
        if not customer_id or not receipt_id:
            print("\n❌ CRITICAL: Setup failed, cannot continue")
            cleanup_all(token)
            return
        
        # SCENARIO 2: Verify available
        results["scenario_2"] = test_scenario_2_verify_available(token, customer_id, receipt_id)
        
        # SCENARIO 3: Partial on sale
        sale_id = test_scenario_3_partial_on_sale(token, customer_id, receipt_id)
        results["scenario_3"] = sale_id is not None
        
        # SCENARIO 4: Remaining still listed
        results["scenario_4"] = test_scenario_4_remaining_still_listed(token, customer_id, receipt_id)
        
        # SCENARIO 5: Rest on invoice
        invoice_id = test_scenario_5_rest_on_invoice(token, customer_id, receipt_id)
        results["scenario_5"] = invoice_id is not None
        
        # SCENARIO 6: Fully consumed
        results["scenario_6"] = test_scenario_6_fully_consumed(token, customer_id, receipt_id)
        
        # SCENARIO 7: Over-allocation cap
        results["scenario_7"] = test_scenario_7_over_allocation_cap(token)
        
        # SCENARIO 8: Cross-customer safety
        results["scenario_8"] = test_scenario_8_cross_customer_safety(token)
        
        # SCENARIO 9: Legacy attach_receipt_ids
        results["scenario_9"] = test_scenario_9_legacy_attach_receipt_ids(token)
        
        # SCENARIO 10: Regression
        results["scenario_10"] = test_scenario_10_regression(token)
        
        # Cleanup
        cleanup_all(token)
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for scenario, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{scenario}: {status}")
        
        print(f"\nTotal: {passed}/{total} scenarios passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        try:
            cleanup_all(token)
        except:
            pass

if __name__ == "__main__":
    main()
