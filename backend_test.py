#!/usr/bin/env python3
"""
Backend test for invoice advance_applied + balance_due feature.
Tests the NEW invoice fields: advance_applied and balance_due.
"""
import requests
import json
import sys

# Configuration
BASE_URL = "https://6661bdad-da1a-401e-b57e-0be08928ca8f.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "Admin@2026"

# Test data tracking for cleanup
created_customers = []
created_receipts = []
created_invoices = []

def login():
    """Login and return access token."""
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": USERNAME, "password": PASSWORD})
    if resp.status_code != 200:
        print(f"❌ LOGIN FAILED: {resp.status_code} {resp.text}")
        sys.exit(1)
    token = resp.json()["access_token"]
    print(f"✅ Logged in as {USERNAME}")
    return token

def headers(token):
    """Return authorization headers."""
    return {"Authorization": f"Bearer {token}"}

def cleanup(token):
    """Delete all test data created during testing."""
    print("\n🧹 CLEANUP: Deleting test data...")
    h = headers(token)
    
    # Delete invoices
    for inv_id in created_invoices:
        resp = requests.delete(f"{BASE_URL}/invoices/{inv_id}", headers=h)
        if resp.status_code in [200, 204]:
            print(f"  ✅ Deleted invoice {inv_id}")
        else:
            print(f"  ⚠️  Failed to delete invoice {inv_id}: {resp.status_code}")
    
    # Delete receipts
    for rec_id in created_receipts:
        resp = requests.delete(f"{BASE_URL}/receipts/{rec_id}", headers=h)
        if resp.status_code in [200, 204]:
            print(f"  ✅ Deleted receipt {rec_id}")
        else:
            print(f"  ⚠️  Failed to delete receipt {rec_id}: {resp.status_code}")
    
    # Delete customers
    for cust_id in created_customers:
        resp = requests.delete(f"{BASE_URL}/customers/{cust_id}", headers=h)
        if resp.status_code in [200, 204]:
            print(f"  ✅ Deleted customer {cust_id}")
        else:
            print(f"  ⚠️  Failed to delete customer {cust_id}: {resp.status_code}")
    
    print("✅ Cleanup complete\n")

def test_scenario_1_setup(token):
    """SCENARIO 1: Create customer and advance receipt."""
    print("\n" + "="*80)
    print("SCENARIO 1: SETUP - Create customer + advance receipt")
    print("="*80)
    h = headers(token)
    
    # Create customer
    cust_body = {
        "name": "BalDue Test",
        "phone": "9993330001",
        "address": "x"
    }
    resp = requests.post(f"{BASE_URL}/customers", json=cust_body, headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to create customer: {resp.status_code} {resp.text}")
        return None, None
    
    customer = resp.json()
    cust_id = customer["id"]
    created_customers.append(cust_id)
    print(f"✅ Created customer: {customer['name']} (ID: {cust_id})")
    
    # Create advance receipt (source_type='other', no reference_no)
    receipt_body = {
        "customer_id": cust_id,
        "customer_name": "BalDue Test",
        "customer_mobile": "9993330001",
        "amount": 3000,
        "payment_mode": "cash",
        "source_type": "other"
    }
    resp = requests.post(f"{BASE_URL}/receipts", json=receipt_body, headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to create advance receipt: {resp.status_code} {resp.text}")
        return cust_id, None
    
    receipt = resp.json()
    receipt_id = receipt["id"]
    created_receipts.append(receipt_id)
    print(f"✅ Created advance receipt: {receipt['receipt_no']} (ID: {receipt_id}, amount: {receipt['amount']})")
    
    return cust_id, receipt_id

def test_scenario_2_partial_apply(token, cust_id, receipt_id):
    """SCENARIO 2: Partial advance application (2000 of 3000 on 5000 invoice)."""
    print("\n" + "="*80)
    print("SCENARIO 2: PARTIAL APPLY - Apply 2000 of 3000 advance to 5000 invoice")
    print("="*80)
    h = headers(token)
    
    invoice_body = {
        "customer_id": cust_id,
        "customer_name": "BalDue Test",
        "customer_mobile": "9993330001",
        "items": [
            {
                "name": "Cabinet",
                "qty": 1,
                "unit_price": 5000,
                "unit_cost": 0
            }
        ],
        "advance_allocations": [
            {
                "receipt_id": receipt_id,
                "amount": 2000
            }
        ]
    }
    
    resp = requests.post(f"{BASE_URL}/invoices", json=invoice_body, headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to create invoice: {resp.status_code} {resp.text}")
        return None
    
    invoice = resp.json()
    inv_id = invoice["id"]
    created_invoices.append(inv_id)
    
    # Verify response fields
    total = invoice.get("total")
    advance_applied = invoice.get("advance_applied")
    balance_due = invoice.get("balance_due")
    pdf_token = invoice.get("pdf_token")
    
    print(f"✅ Created invoice: {invoice['invoice_no']} (ID: {inv_id})")
    print(f"   Total: {total}")
    print(f"   Advance applied: {advance_applied}")
    print(f"   Balance due: {balance_due}")
    print(f"   PDF token present: {pdf_token is not None}")
    
    # Verify expected values
    errors = []
    if total != 5000:
        errors.append(f"Expected total=5000, got {total}")
    if advance_applied != 2000:
        errors.append(f"Expected advance_applied=2000, got {advance_applied}")
    if balance_due != 3000:
        errors.append(f"Expected balance_due=3000, got {balance_due}")
    if pdf_token is None:
        errors.append("Expected pdf_token to be present (non-null)")
    
    if errors:
        print(f"❌ VERIFICATION FAILED:")
        for err in errors:
            print(f"   - {err}")
        return None
    
    print("✅ SCENARIO 2 PASSED: All fields correct")
    return inv_id

def test_scenario_3_list_reflects_fields(token, inv_id):
    """SCENARIO 3: GET /api/invoices returns advance_applied and balance_due."""
    print("\n" + "="*80)
    print("SCENARIO 3: LIST REFLECTS FIELDS - Verify fields in GET /api/invoices")
    print("="*80)
    h = headers(token)
    
    resp = requests.get(f"{BASE_URL}/invoices", headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to list invoices: {resp.status_code} {resp.text}")
        return False
    
    invoices = resp.json()
    target_invoice = None
    for inv in invoices:
        if inv["id"] == inv_id:
            target_invoice = inv
            break
    
    if not target_invoice:
        print(f"❌ FAILED: Invoice {inv_id} not found in list")
        return False
    
    advance_applied = target_invoice.get("advance_applied")
    balance_due = target_invoice.get("balance_due")
    
    print(f"✅ Found invoice in list: {target_invoice['invoice_no']}")
    print(f"   Advance applied: {advance_applied}")
    print(f"   Balance due: {balance_due}")
    
    errors = []
    if advance_applied != 2000:
        errors.append(f"Expected advance_applied=2000, got {advance_applied}")
    if balance_due != 3000:
        errors.append(f"Expected balance_due=3000, got {balance_due}")
    
    if errors:
        print(f"❌ VERIFICATION FAILED:")
        for err in errors:
            print(f"   - {err}")
        return False
    
    print("✅ SCENARIO 3 PASSED: Fields present in list")
    return True

def test_scenario_4_advance_remaining(token, cust_id, receipt_id):
    """SCENARIO 4: Verify advance remaining balance (allocated=2000, remaining=1000)."""
    print("\n" + "="*80)
    print("SCENARIO 4: ADVANCE REMAINING - Verify receipt shows allocated=2000, remaining=1000")
    print("="*80)
    h = headers(token)
    
    resp = requests.get(f"{BASE_URL}/receipts/advances?customer_id={cust_id}", headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to get advances: {resp.status_code} {resp.text}")
        return False
    
    data = resp.json()
    advances = data.get("advances", [])
    
    target_receipt = None
    for adv in advances:
        if adv["id"] == receipt_id:
            target_receipt = adv
            break
    
    if not target_receipt:
        print(f"❌ FAILED: Receipt {receipt_id} not found in advances list")
        return False
    
    allocated = target_receipt.get("allocated")
    remaining = target_receipt.get("remaining")
    
    print(f"✅ Found receipt in advances: {target_receipt['receipt_no']}")
    print(f"   Allocated: {allocated}")
    print(f"   Remaining: {remaining}")
    
    errors = []
    if allocated != 2000:
        errors.append(f"Expected allocated=2000, got {allocated}")
    if remaining != 1000:
        errors.append(f"Expected remaining=1000, got {remaining}")
    
    if errors:
        print(f"❌ VERIFICATION FAILED:")
        for err in errors:
            print(f"   - {err}")
        return False
    
    print("✅ SCENARIO 4 PASSED: Advance remaining balance correct")
    return True

def test_scenario_5_full_apply(token, cust_id):
    """SCENARIO 5: Full advance application (exact match: 4000 advance on 4000 invoice)."""
    print("\n" + "="*80)
    print("SCENARIO 5: FULL APPLY (EXACT) - Apply 4000 advance to 4000 invoice")
    print("="*80)
    h = headers(token)
    
    # Create another advance receipt (amount=4000)
    receipt_body = {
        "customer_id": cust_id,
        "customer_name": "BalDue Test",
        "customer_mobile": "9993330001",
        "amount": 4000,
        "payment_mode": "cash",
        "source_type": "other"
    }
    resp = requests.post(f"{BASE_URL}/receipts", json=receipt_body, headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to create advance receipt: {resp.status_code} {resp.text}")
        return False
    
    receipt = resp.json()
    receipt_id2 = receipt["id"]
    created_receipts.append(receipt_id2)
    print(f"✅ Created advance receipt: {receipt['receipt_no']} (ID: {receipt_id2}, amount: {receipt['amount']})")
    
    # Create invoice with items totalling 4000
    invoice_body = {
        "customer_id": cust_id,
        "customer_name": "BalDue Test",
        "customer_mobile": "9993330001",
        "items": [
            {
                "name": "Door",
                "qty": 1,
                "unit_price": 4000,
                "unit_cost": 0
            }
        ],
        "advance_allocations": [
            {
                "receipt_id": receipt_id2,
                "amount": 4000
            }
        ]
    }
    
    resp = requests.post(f"{BASE_URL}/invoices", json=invoice_body, headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to create invoice: {resp.status_code} {resp.text}")
        return False
    
    invoice = resp.json()
    inv_id = invoice["id"]
    created_invoices.append(inv_id)
    
    total = invoice.get("total")
    advance_applied = invoice.get("advance_applied")
    balance_due = invoice.get("balance_due")
    
    print(f"✅ Created invoice: {invoice['invoice_no']} (ID: {inv_id})")
    print(f"   Total: {total}")
    print(f"   Advance applied: {advance_applied}")
    print(f"   Balance due: {balance_due}")
    
    errors = []
    if total != 4000:
        errors.append(f"Expected total=4000, got {total}")
    if advance_applied != 4000:
        errors.append(f"Expected advance_applied=4000, got {advance_applied}")
    if balance_due != 0:
        errors.append(f"Expected balance_due=0, got {balance_due}")
    
    if errors:
        print(f"❌ VERIFICATION FAILED:")
        for err in errors:
            print(f"   - {err}")
        return False
    
    print("✅ SCENARIO 5 PASSED: Full advance application (exact match)")
    return True

def test_scenario_6_over_apply_cap(token, cust_id):
    """SCENARIO 6: Over-apply cap (10000 advance, apply 9000 to 6000 invoice)."""
    print("\n" + "="*80)
    print("SCENARIO 6: OVER-APPLY CAP - Apply 9000 of 10000 advance to 6000 invoice")
    print("="*80)
    h = headers(token)
    
    # Create advance receipt (amount=10000)
    receipt_body = {
        "customer_id": cust_id,
        "customer_name": "BalDue Test",
        "customer_mobile": "9993330001",
        "amount": 10000,
        "payment_mode": "cash",
        "source_type": "other"
    }
    resp = requests.post(f"{BASE_URL}/receipts", json=receipt_body, headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to create advance receipt: {resp.status_code} {resp.text}")
        return False
    
    receipt = resp.json()
    receipt_id3 = receipt["id"]
    created_receipts.append(receipt_id3)
    print(f"✅ Created advance receipt: {receipt['receipt_no']} (ID: {receipt_id3}, amount: {receipt['amount']})")
    
    # Create invoice with items totalling 6000, try to apply 9000
    invoice_body = {
        "customer_id": cust_id,
        "customer_name": "BalDue Test",
        "customer_mobile": "9993330001",
        "items": [
            {
                "name": "Table",
                "qty": 1,
                "unit_price": 6000,
                "unit_cost": 0
            }
        ],
        "advance_allocations": [
            {
                "receipt_id": receipt_id3,
                "amount": 9000
            }
        ]
    }
    
    resp = requests.post(f"{BASE_URL}/invoices", json=invoice_body, headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to create invoice: {resp.status_code} {resp.text}")
        return False
    
    invoice = resp.json()
    inv_id = invoice["id"]
    created_invoices.append(inv_id)
    
    total = invoice.get("total")
    advance_applied = invoice.get("advance_applied")
    balance_due = invoice.get("balance_due")
    
    print(f"✅ Created invoice: {invoice['invoice_no']} (ID: {inv_id})")
    print(f"   Total: {total}")
    print(f"   Advance applied: {advance_applied}")
    print(f"   Balance due: {balance_due}")
    
    # Note: balance_due = total - advance_applied = 6000 - 9000 = -3000 (negative is acceptable)
    errors = []
    if total != 6000:
        errors.append(f"Expected total=6000, got {total}")
    if advance_applied != 9000:
        errors.append(f"Expected advance_applied=9000 (capped at min(9000, remaining 10000)), got {advance_applied}")
    if balance_due != -3000:
        errors.append(f"Expected balance_due=-3000 (6000-9000), got {balance_due}")
    
    if errors:
        print(f"❌ VERIFICATION FAILED:")
        for err in errors:
            print(f"   - {err}")
        return False
    
    # Verify receipt remaining
    resp = requests.get(f"{BASE_URL}/receipts/advances?customer_id={cust_id}", headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to get advances: {resp.status_code} {resp.text}")
        return False
    
    data = resp.json()
    advances = data.get("advances", [])
    target_receipt = None
    for adv in advances:
        if adv["id"] == receipt_id3:
            target_receipt = adv
            break
    
    if not target_receipt:
        print(f"❌ FAILED: Receipt {receipt_id3} not found in advances list")
        return False
    
    remaining = target_receipt.get("remaining")
    print(f"   Receipt remaining: {remaining}")
    
    if remaining != 1000:
        print(f"❌ VERIFICATION FAILED: Expected remaining=1000 (10000-9000), got {remaining}")
        return False
    
    print("✅ SCENARIO 6 PASSED: Over-apply capped correctly, balance_due negative as expected")
    return True

def test_scenario_7_no_advance(token):
    """SCENARIO 7: No advance (regression) - invoice without advance fields."""
    print("\n" + "="*80)
    print("SCENARIO 7: NO ADVANCE (REGRESSION) - Invoice without advance")
    print("="*80)
    h = headers(token)
    
    # Create fresh customer
    cust_body = {
        "name": "NoAdvance Test",
        "phone": "9993330002",
        "address": "y"
    }
    resp = requests.post(f"{BASE_URL}/customers", json=cust_body, headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to create customer: {resp.status_code} {resp.text}")
        return False
    
    customer = resp.json()
    cust_id = customer["id"]
    created_customers.append(cust_id)
    print(f"✅ Created customer: {customer['name']} (ID: {cust_id})")
    
    # Create invoice without advance fields
    invoice_body = {
        "customer_id": cust_id,
        "customer_name": "NoAdvance Test",
        "customer_mobile": "9993330002",
        "items": [
            {
                "name": "Chair",
                "qty": 2,
                "unit_price": 1500,
                "unit_cost": 0
            }
        ]
    }
    
    resp = requests.post(f"{BASE_URL}/invoices", json=invoice_body, headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to create invoice: {resp.status_code} {resp.text}")
        return False
    
    invoice = resp.json()
    inv_id = invoice["id"]
    created_invoices.append(inv_id)
    
    total = invoice.get("total")
    advance_applied = invoice.get("advance_applied")
    balance_due = invoice.get("balance_due")
    pdf_token = invoice.get("pdf_token")
    
    print(f"✅ Created invoice: {invoice['invoice_no']} (ID: {inv_id})")
    print(f"   Total: {total}")
    print(f"   Advance applied: {advance_applied}")
    print(f"   Balance due: {balance_due}")
    print(f"   PDF token present: {pdf_token is not None}")
    
    errors = []
    if total != 3000:
        errors.append(f"Expected total=3000 (2*1500), got {total}")
    if advance_applied != 0:
        errors.append(f"Expected advance_applied=0, got {advance_applied}")
    if balance_due != total:
        errors.append(f"Expected balance_due={total}, got {balance_due}")
    if pdf_token is None:
        errors.append("Expected pdf_token to be present (non-null)")
    
    if errors:
        print(f"❌ VERIFICATION FAILED:")
        for err in errors:
            print(f"   - {err}")
        return False
    
    print("✅ SCENARIO 7 PASSED: No advance regression test passed")
    return True

def test_scenario_8_legacy_attach_receipt_ids(token):
    """SCENARIO 8: Legacy attach_receipt_ids (full advance application)."""
    print("\n" + "="*80)
    print("SCENARIO 8: LEGACY attach_receipt_ids - Full advance application")
    print("="*80)
    h = headers(token)
    
    # Create customer
    cust_body = {
        "name": "Legacy Test",
        "phone": "9993330003",
        "address": "z"
    }
    resp = requests.post(f"{BASE_URL}/customers", json=cust_body, headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to create customer: {resp.status_code} {resp.text}")
        return False
    
    customer = resp.json()
    cust_id = customer["id"]
    created_customers.append(cust_id)
    print(f"✅ Created customer: {customer['name']} (ID: {cust_id})")
    
    # Create advance receipt (amount=1500)
    receipt_body = {
        "customer_id": cust_id,
        "customer_name": "Legacy Test",
        "customer_mobile": "9993330003",
        "amount": 1500,
        "payment_mode": "cash",
        "source_type": "other"
    }
    resp = requests.post(f"{BASE_URL}/receipts", json=receipt_body, headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to create advance receipt: {resp.status_code} {resp.text}")
        return False
    
    receipt = resp.json()
    receipt_id = receipt["id"]
    created_receipts.append(receipt_id)
    print(f"✅ Created advance receipt: {receipt['receipt_no']} (ID: {receipt_id}, amount: {receipt['amount']})")
    
    # Create invoice with items totalling 5000, use legacy attach_receipt_ids
    invoice_body = {
        "customer_id": cust_id,
        "customer_name": "Legacy Test",
        "customer_mobile": "9993330003",
        "items": [
            {
                "name": "Sofa",
                "qty": 1,
                "unit_price": 5000,
                "unit_cost": 0
            }
        ],
        "attach_receipt_ids": [receipt_id]  # Legacy: applies full remaining
    }
    
    resp = requests.post(f"{BASE_URL}/invoices", json=invoice_body, headers=h)
    if resp.status_code != 200:
        print(f"❌ FAILED to create invoice: {resp.status_code} {resp.text}")
        return False
    
    invoice = resp.json()
    inv_id = invoice["id"]
    created_invoices.append(inv_id)
    
    total = invoice.get("total")
    advance_applied = invoice.get("advance_applied")
    balance_due = invoice.get("balance_due")
    
    print(f"✅ Created invoice: {invoice['invoice_no']} (ID: {inv_id})")
    print(f"   Total: {total}")
    print(f"   Advance applied: {advance_applied}")
    print(f"   Balance due: {balance_due}")
    
    errors = []
    if total != 5000:
        errors.append(f"Expected total=5000, got {total}")
    if advance_applied != 1500:
        errors.append(f"Expected advance_applied=1500 (full remaining applied), got {advance_applied}")
    if balance_due != 3500:
        errors.append(f"Expected balance_due=3500 (5000-1500), got {balance_due}")
    
    if errors:
        print(f"❌ VERIFICATION FAILED:")
        for err in errors:
            print(f"   - {err}")
        return False
    
    print("✅ SCENARIO 8 PASSED: Legacy attach_receipt_ids works correctly")
    return True

def test_scenario_9_regression(token, cust_id):
    """SCENARIO 9: Regression checks - other endpoints still work."""
    print("\n" + "="*80)
    print("SCENARIO 9: REGRESSION - Verify other endpoints still work")
    print("="*80)
    h = headers(token)
    
    errors = []
    
    # Test GET /api/sales
    resp = requests.get(f"{BASE_URL}/sales", headers=h)
    if resp.status_code != 200:
        errors.append(f"GET /api/sales failed: {resp.status_code}")
    else:
        print(f"✅ GET /api/sales: 200 OK")
    
    # Test GET /api/stats/sales-today
    resp = requests.get(f"{BASE_URL}/stats/sales-today", headers=h)
    if resp.status_code != 200:
        errors.append(f"GET /api/stats/sales-today failed: {resp.status_code}")
    else:
        print(f"✅ GET /api/stats/sales-today: 200 OK")
    
    # Test GET /api/deliveries
    resp = requests.get(f"{BASE_URL}/deliveries", headers=h)
    if resp.status_code != 200:
        errors.append(f"GET /api/deliveries failed: {resp.status_code}")
    else:
        print(f"✅ GET /api/deliveries: 200 OK")
    
    # Test normal sale with advance_allocations
    # Create advance receipt
    receipt_body = {
        "customer_id": cust_id,
        "customer_name": "BalDue Test",
        "customer_mobile": "9993330001",
        "amount": 500,
        "payment_mode": "cash",
        "source_type": "other"
    }
    resp = requests.post(f"{BASE_URL}/receipts", json=receipt_body, headers=h)
    if resp.status_code != 200:
        errors.append(f"Failed to create advance receipt for sale test: {resp.status_code}")
    else:
        receipt = resp.json()
        receipt_id = receipt["id"]
        created_receipts.append(receipt_id)
        
        # Create sale with advance_allocations
        sale_body = {
            "customer_name": "BalDue Test",
            "customer_mobile": "9993330001",
            "amount": 1000,
            "product": "Test Product",
            "advance_allocations": [
                {
                    "receipt_id": receipt_id,
                    "amount": 500
                }
            ]
        }
        resp = requests.post(f"{BASE_URL}/sales", json=sale_body, headers=h)
        if resp.status_code != 200:
            errors.append(f"Failed to create sale with advance_allocations: {resp.status_code}")
        else:
            sale = resp.json()
            print(f"✅ Created sale with advance_allocations: {sale['id']}")
            
            # Verify linked_receipts shows the advance
            if "linked_receipts" in sale:
                advance_receipts = [r for r in sale["linked_receipts"] if r.get("is_advance")]
                if advance_receipts:
                    print(f"✅ Sale.linked_receipts contains advance entry")
                else:
                    errors.append("Sale.linked_receipts does not contain advance entry")
            else:
                errors.append("Sale does not have linked_receipts field")
    
    if errors:
        print(f"❌ REGRESSION TESTS FAILED:")
        for err in errors:
            print(f"   - {err}")
        return False
    
    print("✅ SCENARIO 9 PASSED: All regression tests passed")
    return True

def main():
    """Run all test scenarios."""
    print("\n" + "="*80)
    print("INVOICE ADVANCE APPLIED + BALANCE DUE BACKEND TEST")
    print("="*80)
    
    token = login()
    
    try:
        # Scenario 1: Setup
        cust_id, receipt_id = test_scenario_1_setup(token)
        if not cust_id or not receipt_id:
            print("\n❌ SETUP FAILED - Cannot continue")
            cleanup(token)
            sys.exit(1)
        
        # Scenario 2: Partial apply
        inv_id = test_scenario_2_partial_apply(token, cust_id, receipt_id)
        if not inv_id:
            print("\n❌ SCENARIO 2 FAILED")
            cleanup(token)
            sys.exit(1)
        
        # Scenario 3: List reflects fields
        if not test_scenario_3_list_reflects_fields(token, inv_id):
            print("\n❌ SCENARIO 3 FAILED")
            cleanup(token)
            sys.exit(1)
        
        # Scenario 4: Advance remaining
        if not test_scenario_4_advance_remaining(token, cust_id, receipt_id):
            print("\n❌ SCENARIO 4 FAILED")
            cleanup(token)
            sys.exit(1)
        
        # Scenario 5: Full apply (exact)
        if not test_scenario_5_full_apply(token, cust_id):
            print("\n❌ SCENARIO 5 FAILED")
            cleanup(token)
            sys.exit(1)
        
        # Scenario 6: Over-apply cap
        if not test_scenario_6_over_apply_cap(token, cust_id):
            print("\n❌ SCENARIO 6 FAILED")
            cleanup(token)
            sys.exit(1)
        
        # Scenario 7: No advance (regression)
        if not test_scenario_7_no_advance(token):
            print("\n❌ SCENARIO 7 FAILED")
            cleanup(token)
            sys.exit(1)
        
        # Scenario 8: Legacy attach_receipt_ids
        if not test_scenario_8_legacy_attach_receipt_ids(token):
            print("\n❌ SCENARIO 8 FAILED")
            cleanup(token)
            sys.exit(1)
        
        # Scenario 9: Regression
        if not test_scenario_9_regression(token, cust_id):
            print("\n❌ SCENARIO 9 FAILED")
            cleanup(token)
            sys.exit(1)
        
        # All tests passed
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED (9/9 scenarios)")
        print("="*80)
        
    finally:
        # Always cleanup
        cleanup(token)

if __name__ == "__main__":
    main()
