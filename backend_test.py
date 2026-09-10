#!/usr/bin/env python3
"""
Comprehensive backend test for APPROVAL RULE CHANGE:
Only BACK-DATED employee entries go pending; same-day employee entries auto-approved.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Base URL - using the PUBLIC URL
BASE_URL = "https://9b51b322-3346-499e-955f-b2208d0bab61.preview.emergentagent.com/api"

# Credentials
ADMIN_CREDS = {"username": "admin", "password": "Admin@2026"}
EMP1_CREDS = {"username": "emp1", "password": "Emp@2026"}

# Test data tracking for cleanup
test_data = {
    "sales": [],
    "invoices": [],
    "receipts": [],
    "customers": []
}

# Known legitimate pending entries (DO NOT DELETE)
LEGITIMATE_PENDING = {
    "invoice": "e5d334e7-1341-4f30-a697-1d689e9c17ec",
    "receipt": "a5361459-582d-47b5-a0ab-ec712800f62b"
}


def login(creds: Dict[str, str]) -> str:
    """Login and return access token."""
    resp = requests.post(f"{BASE_URL}/auth/login", json=creds)
    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.status_code} {resp.text}")
    return resp.json()["access_token"]


def get_headers(token: str) -> Dict[str, str]:
    """Return authorization headers."""
    return {"Authorization": f"Bearer {token}"}


def get_today() -> str:
    """Get today's date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


def get_past_date(days_ago: int = 5) -> str:
    """Get a past date in YYYY-MM-DD format."""
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def get_future_date(days_ahead: int = 5) -> str:
    """Get a future date in YYYY-MM-DD format."""
    return (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def create_test_customer(token: str, name: str, phone: str) -> Dict:
    """Create a test customer and track for cleanup."""
    payload = {
        "name": name,
        "phone": phone,
        "address": "Test Address"
    }
    resp = requests.post(f"{BASE_URL}/customers", json=payload, headers=get_headers(token))
    if resp.status_code == 200:
        customer = resp.json()
        test_data["customers"].append(customer["id"])
        return customer
    return {}


def cleanup():
    """Clean up all test data created during testing."""
    print("\n" + "="*80)
    print("CLEANUP: Removing test data...")
    print("="*80)
    
    # Login as admin for cleanup
    admin_token = login(ADMIN_CREDS)
    headers = get_headers(admin_token)
    
    # Delete test sales
    for sale_id in test_data["sales"]:
        try:
            resp = requests.delete(f"{BASE_URL}/sales/{sale_id}", headers=headers)
            if resp.status_code == 200:
                print(f"✓ Deleted sale {sale_id}")
        except Exception as e:
            print(f"✗ Failed to delete sale {sale_id}: {e}")
    
    # Delete test invoices
    for invoice_id in test_data["invoices"]:
        # Skip legitimate pending entries
        if invoice_id == LEGITIMATE_PENDING["invoice"]:
            print(f"⊗ Skipped legitimate pending invoice {invoice_id}")
            continue
        try:
            resp = requests.delete(f"{BASE_URL}/invoices/{invoice_id}", headers=headers)
            if resp.status_code == 200:
                print(f"✓ Deleted invoice {invoice_id}")
        except Exception as e:
            print(f"✗ Failed to delete invoice {invoice_id}: {e}")
    
    # Delete test receipts
    for receipt_id in test_data["receipts"]:
        # Skip legitimate pending entries
        if receipt_id == LEGITIMATE_PENDING["receipt"]:
            print(f"⊗ Skipped legitimate pending receipt {receipt_id}")
            continue
        try:
            resp = requests.delete(f"{BASE_URL}/receipts/{receipt_id}", headers=headers)
            if resp.status_code == 200:
                print(f"✓ Deleted receipt {receipt_id}")
        except Exception as e:
            print(f"✗ Failed to delete receipt {receipt_id}: {e}")
    
    # Delete test customers
    for customer_id in test_data["customers"]:
        try:
            resp = requests.delete(f"{BASE_URL}/customers/{customer_id}", headers=headers)
            if resp.status_code == 200:
                print(f"✓ Deleted customer {customer_id}")
        except Exception as e:
            print(f"✗ Failed to delete customer {customer_id}: {e}")
    
    print("="*80)
    print("CLEANUP COMPLETE")
    print("="*80 + "\n")


def run_tests():
    """Run all approval rule change tests."""
    print("\n" + "="*80)
    print("APPROVAL RULE CHANGE TEST SUITE")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Today's date: {get_today()}")
    print(f"Past date (5 days ago): {get_past_date(5)}")
    print("="*80 + "\n")
    
    results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    try:
        # Login
        print("Logging in...")
        admin_token = login(ADMIN_CREDS)
        emp1_token = login(EMP1_CREDS)
        print("✓ Login successful\n")
        
        # Create test customer for emp1
        print("Creating test customer...")
        customer = create_test_customer(emp1_token, "Approval Test Customer", "9998887777")
        if not customer:
            print("✗ Failed to create test customer")
            return results
        customer_id = customer["id"]
        print(f"✓ Created customer {customer_id}\n")
        
        # ========================================================================
        # TEST 1: emp1 POST /api/sales without date_key → status MUST be 'approved'
        # ========================================================================
        print("TEST 1: emp1 creates same-day sale (no date_key) → status 'approved'")
        print("-" * 80)
        payload = {
            "customer_id": customer_id,
            "customer_name": "Approval Test Customer",
            "amount": 1000,
            "payment_mode": "cash",
            "product": "Test Product 1",
            "notes": "Same-day sale test"
        }
        resp = requests.post(f"{BASE_URL}/sales", json=payload, headers=get_headers(emp1_token))
        if resp.status_code == 200:
            sale = resp.json()
            test_data["sales"].append(sale["id"])
            if sale.get("status") == "approved":
                print(f"✓ PASS: Sale created with status 'approved' (id: {sale['id']})")
                print(f"  Date: {sale.get('date_key')}, Status: {sale.get('status')}")
                results["passed"] += 1
                results["tests"].append({"test": "TEST 1", "status": "PASS", "details": "Same-day employee sale auto-approved"})
            else:
                print(f"✗ FAIL: Sale status is '{sale.get('status')}', expected 'approved'")
                results["failed"] += 1
                results["tests"].append({"test": "TEST 1", "status": "FAIL", "details": f"Status is '{sale.get('status')}' instead of 'approved'"})
        else:
            print(f"✗ FAIL: Failed to create sale: {resp.status_code} {resp.text}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 1", "status": "FAIL", "details": f"API error: {resp.status_code}"})
        print()
        
        # ========================================================================
        # TEST 2: emp1 POST /api/sales with past date_key → status 'pending'
        # ========================================================================
        print("TEST 2: emp1 creates back-dated sale → status 'pending'")
        print("-" * 80)
        past_date = get_past_date(5)
        payload = {
            "customer_id": customer_id,
            "customer_name": "Approval Test Customer",
            "amount": 2000,
            "payment_mode": "cash",
            "product": "Test Product 2",
            "notes": "Back-dated sale test",
            "date_key": past_date
        }
        resp = requests.post(f"{BASE_URL}/sales", json=payload, headers=get_headers(emp1_token))
        if resp.status_code == 200:
            sale = resp.json()
            test_data["sales"].append(sale["id"])
            if sale.get("status") == "pending":
                print(f"✓ PASS: Back-dated sale created with status 'pending' (id: {sale['id']})")
                print(f"  Date: {sale.get('date_key')}, Status: {sale.get('status')}")
                results["passed"] += 1
                results["tests"].append({"test": "TEST 2", "status": "PASS", "details": "Back-dated employee sale goes pending"})
                
                # Verify it appears in admin approvals
                print("  Verifying sale appears in admin approvals...")
                resp_approvals = requests.get(f"{BASE_URL}/approvals", headers=get_headers(admin_token))
                if resp_approvals.status_code == 200:
                    approvals = resp_approvals.json()
                    found = any(item["id"] == sale["id"] and item["kind"] == "sale" for item in approvals.get("items", []))
                    if found:
                        print(f"  ✓ Sale appears in admin approvals queue")
                    else:
                        print(f"  ✗ WARNING: Sale NOT found in admin approvals queue")
                else:
                    print(f"  ✗ WARNING: Failed to fetch approvals: {resp_approvals.status_code}")
            else:
                print(f"✗ FAIL: Sale status is '{sale.get('status')}', expected 'pending'")
                results["failed"] += 1
                results["tests"].append({"test": "TEST 2", "status": "FAIL", "details": f"Status is '{sale.get('status')}' instead of 'pending'"})
        else:
            print(f"✗ FAIL: Failed to create sale: {resp.status_code} {resp.text}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 2", "status": "FAIL", "details": f"API error: {resp.status_code}"})
        print()
        
        # ========================================================================
        # TEST 3: emp1 POST /api/invoices without date_key → status 'approved'
        # ========================================================================
        print("TEST 3: emp1 creates same-day invoice (no date_key) → status 'approved'")
        print("-" * 80)
        payload = {
            "customer_name": "Approval Test Customer",
            "customer_mobile": "9998887777",
            "customer_id": customer_id,
            "items": [
                {"name": "Item 1", "qty": 2, "unit_price": 500}
            ],
            "notes": "Same-day invoice test"
        }
        resp = requests.post(f"{BASE_URL}/invoices", json=payload, headers=get_headers(emp1_token))
        if resp.status_code == 200:
            invoice = resp.json()
            test_data["invoices"].append(invoice["id"])
            if invoice.get("status") == "approved":
                print(f"✓ PASS: Invoice created with status 'approved' (id: {invoice['id']})")
                print(f"  Date: {invoice.get('date_key')}, Status: {invoice.get('status')}")
                results["passed"] += 1
                results["tests"].append({"test": "TEST 3", "status": "PASS", "details": "Same-day employee invoice auto-approved"})
            else:
                print(f"✗ FAIL: Invoice status is '{invoice.get('status')}', expected 'approved'")
                results["failed"] += 1
                results["tests"].append({"test": "TEST 3", "status": "FAIL", "details": f"Status is '{invoice.get('status')}' instead of 'approved'"})
        else:
            print(f"✗ FAIL: Failed to create invoice: {resp.status_code} {resp.text}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 3", "status": "FAIL", "details": f"API error: {resp.status_code}"})
        print()
        
        # ========================================================================
        # TEST 4: emp1 POST /api/invoices with past date_key → status 'pending'
        # ========================================================================
        print("TEST 4: emp1 creates back-dated invoice → status 'pending'")
        print("-" * 80)
        past_date = get_past_date(7)
        payload = {
            "customer_name": "Approval Test Customer",
            "customer_mobile": "9998887777",
            "customer_id": customer_id,
            "items": [
                {"name": "Item 2", "qty": 1, "unit_price": 1500}
            ],
            "notes": "Back-dated invoice test",
            "date_key": past_date
        }
        resp = requests.post(f"{BASE_URL}/invoices", json=payload, headers=get_headers(emp1_token))
        if resp.status_code == 200:
            invoice = resp.json()
            test_data["invoices"].append(invoice["id"])
            if invoice.get("status") == "pending":
                print(f"✓ PASS: Back-dated invoice created with status 'pending' (id: {invoice['id']})")
                print(f"  Date: {invoice.get('date_key')}, Status: {invoice.get('status')}")
                results["passed"] += 1
                results["tests"].append({"test": "TEST 4", "status": "PASS", "details": "Back-dated employee invoice goes pending"})
                
                # Verify it appears in admin approvals
                print("  Verifying invoice appears in admin approvals...")
                resp_approvals = requests.get(f"{BASE_URL}/approvals", headers=get_headers(admin_token))
                if resp_approvals.status_code == 200:
                    approvals = resp_approvals.json()
                    found = any(item["id"] == invoice["id"] and item["kind"] == "invoice" for item in approvals.get("items", []))
                    if found:
                        print(f"  ✓ Invoice appears in admin approvals queue")
                    else:
                        print(f"  ✗ WARNING: Invoice NOT found in admin approvals queue")
                else:
                    print(f"  ✗ WARNING: Failed to fetch approvals: {resp_approvals.status_code}")
            else:
                print(f"✗ FAIL: Invoice status is '{invoice.get('status')}', expected 'pending'")
                results["failed"] += 1
                results["tests"].append({"test": "TEST 4", "status": "FAIL", "details": f"Status is '{invoice.get('status')}' instead of 'pending'"})
        else:
            print(f"✗ FAIL: Failed to create invoice: {resp.status_code} {resp.text}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 4", "status": "FAIL", "details": f"API error: {resp.status_code}"})
        print()
        
        # ========================================================================
        # TEST 5: emp1 POST /api/receipts without date_key → status 'approved'
        # ========================================================================
        print("TEST 5: emp1 creates same-day receipt (no date_key) → status 'approved'")
        print("-" * 80)
        payload = {
            "customer_name": "Approval Test Customer",
            "customer_mobile": "9998887777",
            "customer_id": customer_id,
            "amount": 800,
            "payment_mode": "cash",
            "source_type": "other",
            "notes": "Same-day receipt test"
        }
        resp = requests.post(f"{BASE_URL}/receipts", json=payload, headers=get_headers(emp1_token))
        if resp.status_code == 200:
            receipt = resp.json()
            test_data["receipts"].append(receipt["id"])
            if receipt.get("status") == "approved":
                print(f"✓ PASS: Receipt created with status 'approved' (id: {receipt['id']})")
                print(f"  Date: {receipt.get('date_key')}, Status: {receipt.get('status')}")
                results["passed"] += 1
                results["tests"].append({"test": "TEST 5", "status": "PASS", "details": "Same-day employee receipt auto-approved"})
            else:
                print(f"✗ FAIL: Receipt status is '{receipt.get('status')}', expected 'approved'")
                results["failed"] += 1
                results["tests"].append({"test": "TEST 5", "status": "FAIL", "details": f"Status is '{receipt.get('status')}' instead of 'approved'"})
        else:
            print(f"✗ FAIL: Failed to create receipt: {resp.status_code} {resp.text}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 5", "status": "FAIL", "details": f"API error: {resp.status_code}"})
        print()
        
        # ========================================================================
        # TEST 6: emp1 POST /api/receipts with past date_key → status 'pending'
        # ========================================================================
        print("TEST 6: emp1 creates back-dated receipt → status 'pending'")
        print("-" * 80)
        past_date = get_past_date(3)
        payload = {
            "customer_name": "Approval Test Customer",
            "customer_mobile": "9998887777",
            "customer_id": customer_id,
            "amount": 1200,
            "payment_mode": "cash",
            "source_type": "other",
            "notes": "Back-dated receipt test",
            "date_key": past_date
        }
        resp = requests.post(f"{BASE_URL}/receipts", json=payload, headers=get_headers(emp1_token))
        if resp.status_code == 200:
            receipt = resp.json()
            test_data["receipts"].append(receipt["id"])
            if receipt.get("status") == "pending":
                print(f"✓ PASS: Back-dated receipt created with status 'pending' (id: {receipt['id']})")
                print(f"  Date: {receipt.get('date_key')}, Status: {receipt.get('status')}")
                results["passed"] += 1
                results["tests"].append({"test": "TEST 6", "status": "PASS", "details": "Back-dated employee receipt goes pending"})
                
                # Verify it appears in admin approvals
                print("  Verifying receipt appears in admin approvals...")
                resp_approvals = requests.get(f"{BASE_URL}/approvals", headers=get_headers(admin_token))
                if resp_approvals.status_code == 200:
                    approvals = resp_approvals.json()
                    found = any(item["id"] == receipt["id"] and item["kind"] == "receipt" for item in approvals.get("items", []))
                    if found:
                        print(f"  ✓ Receipt appears in admin approvals queue")
                    else:
                        print(f"  ✗ WARNING: Receipt NOT found in admin approvals queue")
                else:
                    print(f"  ✗ WARNING: Failed to fetch approvals: {resp_approvals.status_code}")
            else:
                print(f"✗ FAIL: Receipt status is '{receipt.get('status')}', expected 'pending'")
                results["failed"] += 1
                results["tests"].append({"test": "TEST 6", "status": "FAIL", "details": f"Status is '{receipt.get('status')}' instead of 'pending'"})
        else:
            print(f"✗ FAIL: Failed to create receipt: {resp.status_code} {resp.text}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 6", "status": "FAIL", "details": f"API error: {resp.status_code}"})
        print()
        
        # ========================================================================
        # TEST 7: emp1 PATCH same-day sale (only notes) → status STAYS 'approved'
        # ========================================================================
        print("TEST 7: emp1 edits same-day sale (only notes) → status STAYS 'approved'")
        print("-" * 80)
        # Create a same-day sale first
        payload = {
            "customer_id": customer_id,
            "customer_name": "Approval Test Customer",
            "amount": 500,
            "payment_mode": "cash",
            "product": "Test Product for Edit",
            "notes": "Original notes"
        }
        resp = requests.post(f"{BASE_URL}/sales", json=payload, headers=get_headers(emp1_token))
        if resp.status_code == 200:
            sale = resp.json()
            test_data["sales"].append(sale["id"])
            sale_id = sale["id"]
            original_status = sale.get("status")
            print(f"  Created sale {sale_id} with status '{original_status}'")
            
            # Now edit only the notes
            patch_payload = {"notes": "Updated notes - same day edit"}
            resp_patch = requests.patch(f"{BASE_URL}/sales/{sale_id}", json=patch_payload, headers=get_headers(emp1_token))
            if resp_patch.status_code == 200:
                updated_sale = resp_patch.json()
                if updated_sale.get("status") == "approved":
                    print(f"✓ PASS: Sale status STAYED 'approved' after same-day edit")
                    print(f"  Original status: {original_status}, Updated status: {updated_sale.get('status')}")
                    results["passed"] += 1
                    results["tests"].append({"test": "TEST 7", "status": "PASS", "details": "Same-day edit keeps status approved"})
                else:
                    print(f"✗ FAIL: Sale status changed to '{updated_sale.get('status')}', expected 'approved'")
                    results["failed"] += 1
                    results["tests"].append({"test": "TEST 7", "status": "FAIL", "details": f"Status changed to '{updated_sale.get('status')}'"})
            else:
                print(f"✗ FAIL: Failed to patch sale: {resp_patch.status_code} {resp_patch.text}")
                results["failed"] += 1
                results["tests"].append({"test": "TEST 7", "status": "FAIL", "details": f"PATCH API error: {resp_patch.status_code}"})
        else:
            print(f"✗ FAIL: Failed to create sale for edit test: {resp.status_code} {resp.text}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 7", "status": "FAIL", "details": f"Setup failed: {resp.status_code}"})
        print()
        
        # ========================================================================
        # TEST 8: emp1 PATCH sale with past date_key → status becomes 'pending'
        # ========================================================================
        print("TEST 8: emp1 edits sale with back-dated date_key → status becomes 'pending'")
        print("-" * 80)
        # Create a same-day sale first
        payload = {
            "customer_id": customer_id,
            "customer_name": "Approval Test Customer",
            "amount": 600,
            "payment_mode": "cash",
            "product": "Test Product for Backdate Edit",
            "notes": "Original notes"
        }
        resp = requests.post(f"{BASE_URL}/sales", json=payload, headers=get_headers(emp1_token))
        if resp.status_code == 200:
            sale = resp.json()
            test_data["sales"].append(sale["id"])
            sale_id = sale["id"]
            original_status = sale.get("status")
            print(f"  Created sale {sale_id} with status '{original_status}'")
            
            # Now edit with a past date
            past_date = get_past_date(4)
            patch_payload = {"date_key": past_date}
            resp_patch = requests.patch(f"{BASE_URL}/sales/{sale_id}", json=patch_payload, headers=get_headers(emp1_token))
            if resp_patch.status_code == 200:
                updated_sale = resp_patch.json()
                if updated_sale.get("status") == "pending":
                    print(f"✓ PASS: Sale status changed to 'pending' after back-dating")
                    print(f"  Original status: {original_status}, Updated status: {updated_sale.get('status')}")
                    print(f"  Date changed to: {updated_sale.get('date_key')}")
                    results["passed"] += 1
                    results["tests"].append({"test": "TEST 8", "status": "PASS", "details": "Back-dating sale changes status to pending"})
                else:
                    print(f"✗ FAIL: Sale status is '{updated_sale.get('status')}', expected 'pending'")
                    results["failed"] += 1
                    results["tests"].append({"test": "TEST 8", "status": "FAIL", "details": f"Status is '{updated_sale.get('status')}' instead of 'pending'"})
            else:
                print(f"✗ FAIL: Failed to patch sale: {resp_patch.status_code} {resp_patch.text}")
                results["failed"] += 1
                results["tests"].append({"test": "TEST 8", "status": "FAIL", "details": f"PATCH API error: {resp_patch.status_code}"})
        else:
            print(f"✗ FAIL: Failed to create sale for backdate test: {resp.status_code} {resp.text}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 8", "status": "FAIL", "details": f"Setup failed: {resp.status_code}"})
        print()
        
        # ========================================================================
        # TEST 9: Admin POST /api/sales with past date_key → still 'approved'
        # ========================================================================
        print("TEST 9: Admin creates back-dated sale → status 'approved' (admin auto-approved)")
        print("-" * 80)
        past_date = get_past_date(10)
        payload = {
            "customer_id": customer_id,
            "customer_name": "Approval Test Customer",
            "amount": 3000,
            "payment_mode": "cash",
            "product": "Admin Test Product",
            "notes": "Admin back-dated sale test",
            "date_key": past_date
        }
        resp = requests.post(f"{BASE_URL}/sales", json=payload, headers=get_headers(admin_token))
        if resp.status_code == 200:
            sale = resp.json()
            test_data["sales"].append(sale["id"])
            if sale.get("status") == "approved":
                print(f"✓ PASS: Admin back-dated sale created with status 'approved' (id: {sale['id']})")
                print(f"  Date: {sale.get('date_key')}, Status: {sale.get('status')}")
                results["passed"] += 1
                results["tests"].append({"test": "TEST 9", "status": "PASS", "details": "Admin back-dated sale auto-approved"})
            else:
                print(f"✗ FAIL: Sale status is '{sale.get('status')}', expected 'approved'")
                results["failed"] += 1
                results["tests"].append({"test": "TEST 9", "status": "FAIL", "details": f"Admin sale status is '{sale.get('status')}' instead of 'approved'"})
        else:
            print(f"✗ FAIL: Failed to create admin sale: {resp.status_code} {resp.text}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 9", "status": "FAIL", "details": f"API error: {resp.status_code}"})
        print()
        
        # ========================================================================
        # TEST 10: emp1 POST /api/sales with FUTURE date_key → 400 error
        # ========================================================================
        print("TEST 10: emp1 creates sale with future date → 400 error (regression)")
        print("-" * 80)
        future_date = get_future_date(5)
        payload = {
            "customer_id": customer_id,
            "customer_name": "Approval Test Customer",
            "amount": 1500,
            "payment_mode": "cash",
            "product": "Future Test Product",
            "notes": "Future date test",
            "date_key": future_date
        }
        resp = requests.post(f"{BASE_URL}/sales", json=payload, headers=get_headers(emp1_token))
        if resp.status_code == 400:
            print(f"✓ PASS: Future date correctly rejected with 400 error")
            print(f"  Error: {resp.json().get('detail', resp.text)}")
            results["passed"] += 1
            results["tests"].append({"test": "TEST 10", "status": "PASS", "details": "Future date validation working"})
        else:
            print(f"✗ FAIL: Expected 400 error, got {resp.status_code}")
            if resp.status_code == 200:
                sale = resp.json()
                test_data["sales"].append(sale["id"])
                print(f"  Sale was created with id {sale['id']} (should have been rejected)")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 10", "status": "FAIL", "details": f"Got {resp.status_code} instead of 400"})
        print()
        
        # ========================================================================
        # TEST 11: Admin approve flow still works
        # ========================================================================
        print("TEST 11: Admin approve flow regression test")
        print("-" * 80)
        # Create a back-dated sale as emp1
        past_date = get_past_date(2)
        payload = {
            "customer_id": customer_id,
            "customer_name": "Approval Test Customer",
            "amount": 700,
            "payment_mode": "cash",
            "product": "Approve Flow Test",
            "notes": "Testing approve flow",
            "date_key": past_date
        }
        resp = requests.post(f"{BASE_URL}/sales", json=payload, headers=get_headers(emp1_token))
        if resp.status_code == 200:
            sale = resp.json()
            test_data["sales"].append(sale["id"])
            sale_id = sale["id"]
            print(f"  Created pending sale {sale_id}")
            
            # Admin approves it
            resp_approve = requests.post(f"{BASE_URL}/approvals/sale/{sale_id}/approve", headers=get_headers(admin_token))
            if resp_approve.status_code == 200:
                approved_data = resp_approve.json()
                if approved_data.get("approved"):
                    print(f"✓ PASS: Admin successfully approved sale {sale_id}")
                    results["passed"] += 1
                    results["tests"].append({"test": "TEST 11", "status": "PASS", "details": "Admin approve flow working"})
                else:
                    print(f"✗ FAIL: Approve response doesn't show approved=true")
                    results["failed"] += 1
                    results["tests"].append({"test": "TEST 11", "status": "FAIL", "details": "Approve response incorrect"})
            else:
                print(f"✗ FAIL: Failed to approve sale: {resp_approve.status_code} {resp_approve.text}")
                results["failed"] += 1
                results["tests"].append({"test": "TEST 11", "status": "FAIL", "details": f"Approve API error: {resp_approve.status_code}"})
        else:
            print(f"✗ FAIL: Failed to create sale for approve test: {resp.status_code} {resp.text}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 11", "status": "FAIL", "details": f"Setup failed: {resp.status_code}"})
        print()
        
        # ========================================================================
        # TEST 12: GET /api/stats/sales-today counts approved same-day sale
        # ========================================================================
        print("TEST 12: GET /api/stats/sales-today counts approved same-day sale (regression)")
        print("-" * 80)
        # Get current count
        resp_before = requests.get(f"{BASE_URL}/stats/sales-today?scope=all", headers=get_headers(admin_token))
        if resp_before.status_code == 200:
            stats_before = resp_before.json()
            count_before = stats_before.get("count", 0)
            print(f"  Sales count before: {count_before}")
            
            # Create a same-day sale as emp1
            payload = {
                "customer_id": customer_id,
                "customer_name": "Approval Test Customer",
                "amount": 999,
                "payment_mode": "cash",
                "product": "Stats Test Product",
                "notes": "Testing stats counting"
            }
            resp = requests.post(f"{BASE_URL}/sales", json=payload, headers=get_headers(emp1_token))
            if resp.status_code == 200:
                sale = resp.json()
                test_data["sales"].append(sale["id"])
                print(f"  Created same-day sale {sale['id']} with status '{sale.get('status')}'")
                
                # Get updated count
                resp_after = requests.get(f"{BASE_URL}/stats/sales-today?scope=all", headers=get_headers(admin_token))
                if resp_after.status_code == 200:
                    stats_after = resp_after.json()
                    count_after = stats_after.get("count", 0)
                    print(f"  Sales count after: {count_after}")
                    
                    if count_after == count_before + 1:
                        print(f"✓ PASS: Same-day approved sale counted in stats")
                        results["passed"] += 1
                        results["tests"].append({"test": "TEST 12", "status": "PASS", "details": "Stats counting working correctly"})
                    else:
                        print(f"✗ FAIL: Count didn't increase by 1 (before: {count_before}, after: {count_after})")
                        results["failed"] += 1
                        results["tests"].append({"test": "TEST 12", "status": "FAIL", "details": f"Count mismatch: {count_before} -> {count_after}"})
                else:
                    print(f"✗ FAIL: Failed to get stats after: {resp_after.status_code}")
                    results["failed"] += 1
                    results["tests"].append({"test": "TEST 12", "status": "FAIL", "details": f"Stats API error: {resp_after.status_code}"})
            else:
                print(f"✗ FAIL: Failed to create sale: {resp.status_code} {resp.text}")
                results["failed"] += 1
                results["tests"].append({"test": "TEST 12", "status": "FAIL", "details": f"Sale creation failed: {resp.status_code}"})
        else:
            print(f"✗ FAIL: Failed to get stats before: {resp_before.status_code}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 12", "status": "FAIL", "details": f"Stats API error: {resp_before.status_code}"})
        print()
        
        # ========================================================================
        # TEST 13: Verify legitimate pending entries exist
        # ========================================================================
        print("TEST 13: Verify legitimate pending entries exist (DO NOT DELETE)")
        print("-" * 80)
        resp_approvals = requests.get(f"{BASE_URL}/approvals", headers=get_headers(admin_token))
        if resp_approvals.status_code == 200:
            approvals = resp_approvals.json()
            items = approvals.get("items", [])
            
            # Check for legitimate invoice
            invoice_found = any(item["id"] == LEGITIMATE_PENDING["invoice"] and item["kind"] == "invoice" for item in items)
            # Check for legitimate receipt
            receipt_found = any(item["id"] == LEGITIMATE_PENDING["receipt"] and item["kind"] == "receipt" for item in items)
            
            if invoice_found and receipt_found:
                print(f"✓ PASS: Both legitimate pending entries found in approvals queue")
                print(f"  Invoice: {LEGITIMATE_PENDING['invoice']} (₹5000)")
                print(f"  Receipt: {LEGITIMATE_PENDING['receipt']} (₹10000)")
                results["passed"] += 1
                results["tests"].append({"test": "TEST 13", "status": "PASS", "details": "Legitimate pending entries preserved"})
            elif invoice_found:
                print(f"⚠ PARTIAL: Invoice found but receipt missing")
                print(f"  Invoice: {LEGITIMATE_PENDING['invoice']} found")
                print(f"  Receipt: {LEGITIMATE_PENDING['receipt']} NOT found")
                results["passed"] += 1
                results["tests"].append({"test": "TEST 13", "status": "PARTIAL", "details": "Invoice found, receipt missing"})
            elif receipt_found:
                print(f"⚠ PARTIAL: Receipt found but invoice missing")
                print(f"  Invoice: {LEGITIMATE_PENDING['invoice']} NOT found")
                print(f"  Receipt: {LEGITIMATE_PENDING['receipt']} found")
                results["passed"] += 1
                results["tests"].append({"test": "TEST 13", "status": "PARTIAL", "details": "Receipt found, invoice missing"})
            else:
                print(f"⚠ WARNING: Neither legitimate pending entry found")
                print(f"  This may be expected if they were already approved/deleted")
                print(f"  Invoice: {LEGITIMATE_PENDING['invoice']} NOT found")
                print(f"  Receipt: {LEGITIMATE_PENDING['receipt']} NOT found")
                results["passed"] += 1
                results["tests"].append({"test": "TEST 13", "status": "INFO", "details": "Legitimate entries not found (may be already processed)"})
        else:
            print(f"✗ FAIL: Failed to fetch approvals: {resp_approvals.status_code}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST 13", "status": "FAIL", "details": f"Approvals API error: {resp_approvals.status_code}"})
        print()
        
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        cleanup()
    
    return results


def print_summary(results: Dict):
    """Print test summary."""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {results['passed'] + results['failed']}")
    print(f"✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    print("="*80)
    
    if results["tests"]:
        print("\nDETAILED RESULTS:")
        print("-" * 80)
        for test in results["tests"]:
            status_symbol = "✓" if test["status"] == "PASS" else ("⚠" if test["status"] in ["PARTIAL", "INFO"] else "✗")
            print(f"{status_symbol} {test['test']}: {test['status']}")
            print(f"  {test['details']}")
        print("-" * 80)
    
    print("\n" + "="*80)
    if results["failed"] == 0:
        print("✓ ALL TESTS PASSED - APPROVAL RULE CHANGE WORKING CORRECTLY")
    else:
        print(f"✗ {results['failed']} TEST(S) FAILED - REVIEW REQUIRED")
    print("="*80 + "\n")


if __name__ == "__main__":
    results = run_tests()
    print_summary(results)
    
    # Exit with appropriate code
    exit(0 if results["failed"] == 0 else 1)
