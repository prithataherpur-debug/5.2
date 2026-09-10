#!/usr/bin/env python3
"""
Comprehensive backend test for TEAM-STATS ENDPOINT:
GET /api/admin/team-stats with period filter (today/week/month/all)
Per-employee total sell (sales+invoices), revenue, profit + admin row + grand totals
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

# CRITICAL: Known REAL USER DATA - DO NOT DELETE
REAL_USER_DATA = {
    "sale": "36cb7374-128a-41fe-b8ef-d48bf03492c6",  # ₹10000
    "invoice": "e5d334e7-1341-4f30-a697-1d689e9c17ec",  # ₹5000
    "receipt": "a5361459-582d-47b5-a0ab-ec712800f62b"  # ₹10000
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
    
    # Delete test sales (SKIP REAL USER DATA)
    for sale_id in test_data["sales"]:
        if sale_id == REAL_USER_DATA["sale"]:
            print(f"⊗ SKIPPED REAL USER DATA: sale {sale_id}")
            continue
        try:
            resp = requests.delete(f"{BASE_URL}/sales/{sale_id}", headers=headers)
            if resp.status_code == 200:
                print(f"✓ Deleted sale {sale_id}")
        except Exception as e:
            print(f"✗ Failed to delete sale {sale_id}: {e}")
    
    # Delete test invoices (SKIP REAL USER DATA)
    for invoice_id in test_data["invoices"]:
        if invoice_id == REAL_USER_DATA["invoice"]:
            print(f"⊗ SKIPPED REAL USER DATA: invoice {invoice_id}")
            continue
        try:
            resp = requests.delete(f"{BASE_URL}/invoices/{invoice_id}", headers=headers)
            if resp.status_code == 200:
                print(f"✓ Deleted invoice {invoice_id}")
        except Exception as e:
            print(f"✗ Failed to delete invoice {invoice_id}: {e}")
    
    # Delete test receipts (SKIP REAL USER DATA)
    for receipt_id in test_data["receipts"]:
        if receipt_id == REAL_USER_DATA["receipt"]:
            print(f"⊗ SKIPPED REAL USER DATA: receipt {receipt_id}")
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
    """Run all team-stats endpoint tests."""
    print("\n" + "="*80)
    print("TEAM-STATS ENDPOINT TEST SUITE")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Today's date: {get_today()}")
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
        
        # ========================================================================
        # TEST (a): Default (no period param) → period='today'
        # Expected: totals {sales_count:1, invoices_count:0, total_count:1, revenue:10000, profit:500}
        # admin object all zeros; emp1 row has all 5 new fields
        # ========================================================================
        print("TEST (a): GET /api/admin/team-stats (default/no period) → period='today'")
        print("-" * 80)
        resp = requests.get(f"{BASE_URL}/admin/team-stats", headers=get_headers(admin_token))
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ Response 200 OK")
            print(f"  Period: {data.get('period')}")
            print(f"  Totals: {data.get('totals')}")
            print(f"  Admin: {data.get('admin')}")
            
            # Verify period is 'today'
            if data.get('period') == 'today':
                print(f"  ✓ Period is 'today' (default)")
            else:
                print(f"  ✗ Period is '{data.get('period')}', expected 'today'")
            
            # Verify totals structure
            totals = data.get('totals', {})
            expected_totals = {
                "sales_count": 1,
                "invoices_count": 0,
                "total_count": 1,
                "revenue": 10000,
                "profit": 500
            }
            
            totals_match = True
            for key, expected_val in expected_totals.items():
                actual_val = totals.get(key)
                if actual_val == expected_val:
                    print(f"  ✓ totals.{key} = {actual_val} (expected {expected_val})")
                else:
                    print(f"  ✗ totals.{key} = {actual_val}, expected {expected_val}")
                    totals_match = False
            
            # Verify admin object (should be all zeros)
            admin_obj = data.get('admin', {})
            admin_zeros = (
                admin_obj.get('sales_count') == 0 and
                admin_obj.get('invoices_count') == 0 and
                admin_obj.get('total_count') == 0 and
                admin_obj.get('revenue') == 0 and
                admin_obj.get('profit') == 0
            )
            if admin_zeros:
                print(f"  ✓ Admin object all zeros: {admin_obj}")
            else:
                print(f"  ✗ Admin object NOT all zeros: {admin_obj}")
            
            # Verify emp1 row has all 5 new fields
            rows = data.get('rows', [])
            emp1_row = next((r for r in rows if r.get('username') == 'emp1'), None)
            if emp1_row:
                required_fields = ['sales_count', 'invoices_count', 'total_count', 'revenue', 'profit']
                emp1_has_fields = all(field in emp1_row for field in required_fields)
                if emp1_has_fields:
                    print(f"  ✓ emp1 row has all 5 fields: sales_count={emp1_row.get('sales_count')}, invoices_count={emp1_row.get('invoices_count')}, total_count={emp1_row.get('total_count')}, revenue={emp1_row.get('revenue')}, profit={emp1_row.get('profit')}")
                else:
                    print(f"  ✗ emp1 row missing fields: {emp1_row}")
            else:
                print(f"  ✗ emp1 row not found in rows")
                emp1_has_fields = False
            
            if data.get('period') == 'today' and totals_match and admin_zeros and emp1_has_fields:
                print(f"✓ PASS: TEST (a)")
                results["passed"] += 1
                results["tests"].append({"test": "TEST (a)", "status": "PASS", "details": "Default period='today' with correct totals"})
            else:
                print(f"✗ FAIL: TEST (a)")
                results["failed"] += 1
                results["tests"].append({"test": "TEST (a)", "status": "FAIL", "details": "Period or totals mismatch"})
        else:
            print(f"✗ FAIL: Response {resp.status_code} {resp.text}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST (a)", "status": "FAIL", "details": f"API error: {resp.status_code}"})
        print()
        
        # ========================================================================
        # TEST (b): period=week, period=month, period=all
        # Expected: totals {sales_count:1, invoices_count:1, total_count:2, revenue:15000, profit:1500}
        # (₹5000 invoice dated 2026-09-09 = yesterday, excluded from 'today', included in week/month/all)
        # ========================================================================
        for period in ['week', 'month', 'all']:
            print(f"TEST (b.{period}): GET /api/admin/team-stats?period={period}")
            print("-" * 80)
            resp = requests.get(f"{BASE_URL}/admin/team-stats?period={period}", headers=get_headers(admin_token))
            if resp.status_code == 200:
                data = resp.json()
                print(f"✓ Response 200 OK")
                print(f"  Period: {data.get('period')}")
                print(f"  Totals: {data.get('totals')}")
                
                # Verify period
                if data.get('period') == period:
                    print(f"  ✓ Period is '{period}'")
                else:
                    print(f"  ✗ Period is '{data.get('period')}', expected '{period}'")
                
                # Verify totals
                totals = data.get('totals', {})
                expected_totals = {
                    "sales_count": 1,
                    "invoices_count": 1,
                    "total_count": 2,
                    "revenue": 15000,
                    "profit": 1500
                }
                
                totals_match = True
                for key, expected_val in expected_totals.items():
                    actual_val = totals.get(key)
                    if actual_val == expected_val:
                        print(f"  ✓ totals.{key} = {actual_val} (expected {expected_val})")
                    else:
                        print(f"  ✗ totals.{key} = {actual_val}, expected {expected_val}")
                        totals_match = False
                
                if data.get('period') == period and totals_match:
                    print(f"✓ PASS: TEST (b.{period})")
                    results["passed"] += 1
                    results["tests"].append({"test": f"TEST (b.{period})", "status": "PASS", "details": f"period={period} with correct totals"})
                else:
                    print(f"✗ FAIL: TEST (b.{period})")
                    results["failed"] += 1
                    results["tests"].append({"test": f"TEST (b.{period})", "status": "FAIL", "details": "Period or totals mismatch"})
            else:
                print(f"✗ FAIL: Response {resp.status_code} {resp.text}")
                results["failed"] += 1
                results["tests"].append({"test": f"TEST (b.{period})", "status": "FAIL", "details": f"API error: {resp.status_code}"})
            print()
        
        # ========================================================================
        # TEST (c): Create sale as emp1 today → verify totals increase → DELETE
        # ========================================================================
        print("TEST (c): Create sale as emp1 today (amount 1000, purchase_amount 200)")
        print("-" * 80)
        
        # Create test customer
        customer = create_test_customer(emp1_token, "Team Stats Test Customer", "9991112222")
        if not customer:
            print("✗ Failed to create test customer")
            results["failed"] += 1
            results["tests"].append({"test": "TEST (c)", "status": "FAIL", "details": "Customer creation failed"})
        else:
            customer_id = customer["id"]
            print(f"  Created customer {customer_id}")
            
            # Get baseline totals
            resp_before = requests.get(f"{BASE_URL}/admin/team-stats?period=today", headers=get_headers(admin_token))
            if resp_before.status_code == 200:
                totals_before = resp_before.json().get('totals', {})
                revenue_before = totals_before.get('revenue', 0)
                profit_before = totals_before.get('profit', 0)
                print(f"  Baseline: revenue={revenue_before}, profit={profit_before}")
                
                # Create sale
                sale_payload = {
                    "customer_id": customer_id,
                    "customer_name": "Team Stats Test Customer",
                    "amount": 1000,
                    "purchase_amount": 200,
                    "payment_mode": "cash",
                    "product": "Test Product",
                    "notes": "Team stats test sale"
                }
                resp_sale = requests.post(f"{BASE_URL}/sales", json=sale_payload, headers=get_headers(emp1_token))
                if resp_sale.status_code == 200:
                    sale = resp_sale.json()
                    test_data["sales"].append(sale["id"])
                    print(f"  ✓ Created sale {sale['id']}")
                    
                    # Get updated totals
                    resp_after = requests.get(f"{BASE_URL}/admin/team-stats?period=today", headers=get_headers(admin_token))
                    if resp_after.status_code == 200:
                        totals_after = resp_after.json().get('totals', {})
                        revenue_after = totals_after.get('revenue', 0)
                        profit_after = totals_after.get('profit', 0)
                        print(f"  After: revenue={revenue_after}, profit={profit_after}")
                        
                        revenue_increase = revenue_after - revenue_before
                        profit_increase = profit_after - profit_before
                        
                        if revenue_increase == 1000:
                            print(f"  ✓ Revenue increased by 1000 (actual: {revenue_increase})")
                        else:
                            print(f"  ✗ Revenue increased by {revenue_increase}, expected 1000")
                        
                        if profit_increase == 800:
                            print(f"  ✓ Profit increased by 800 (actual: {profit_increase})")
                        else:
                            print(f"  ✗ Profit increased by {profit_increase}, expected 800")
                        
                        if revenue_increase == 1000 and profit_increase == 800:
                            print(f"✓ PASS: TEST (c)")
                            results["passed"] += 1
                            results["tests"].append({"test": "TEST (c)", "status": "PASS", "details": "Sale creation increases totals correctly"})
                        else:
                            print(f"✗ FAIL: TEST (c)")
                            results["failed"] += 1
                            results["tests"].append({"test": "TEST (c)", "status": "FAIL", "details": f"Revenue +{revenue_increase}, Profit +{profit_increase}"})
                    else:
                        print(f"  ✗ Failed to get stats after: {resp_after.status_code}")
                        results["failed"] += 1
                        results["tests"].append({"test": "TEST (c)", "status": "FAIL", "details": "Stats fetch failed"})
                else:
                    print(f"  ✗ Failed to create sale: {resp_sale.status_code} {resp_sale.text}")
                    results["failed"] += 1
                    results["tests"].append({"test": "TEST (c)", "status": "FAIL", "details": "Sale creation failed"})
            else:
                print(f"  ✗ Failed to get baseline stats: {resp_before.status_code}")
                results["failed"] += 1
                results["tests"].append({"test": "TEST (c)", "status": "FAIL", "details": "Baseline stats fetch failed"})
        print()
        
        # ========================================================================
        # TEST (d): Create invoice as admin today → verify admin object and totals → DELETE
        # ========================================================================
        print("TEST (d): Create invoice as admin today (items total 2000, unit_cost 500)")
        print("-" * 80)
        
        # Create test customer
        customer2 = create_test_customer(admin_token, "Admin Invoice Test Customer", "9993334444")
        if not customer2:
            print("✗ Failed to create test customer")
            results["failed"] += 1
            results["tests"].append({"test": "TEST (d)", "status": "FAIL", "details": "Customer creation failed"})
        else:
            customer2_id = customer2["id"]
            print(f"  Created customer {customer2_id}")
            
            # Get baseline
            resp_before = requests.get(f"{BASE_URL}/admin/team-stats?period=today", headers=get_headers(admin_token))
            if resp_before.status_code == 200:
                data_before = resp_before.json()
                admin_before = data_before.get('admin', {})
                totals_before = data_before.get('totals', {})
                print(f"  Baseline admin: {admin_before}")
                print(f"  Baseline totals: {totals_before}")
                
                # Create invoice
                invoice_payload = {
                    "customer_name": "Admin Invoice Test Customer",
                    "customer_mobile": "9993334444",
                    "customer_id": customer2_id,
                    "items": [
                        {
                            "name": "Test Item",
                            "qty": 1,
                            "unit_price": 2000,
                            "unit_cost": 500
                        }
                    ],
                    "notes": "Admin team stats test invoice"
                }
                resp_invoice = requests.post(f"{BASE_URL}/invoices", json=invoice_payload, headers=get_headers(admin_token))
                if resp_invoice.status_code == 200:
                    invoice = resp_invoice.json()
                    test_data["invoices"].append(invoice["id"])
                    print(f"  ✓ Created invoice {invoice['id']}")
                    
                    # Get updated stats
                    resp_after = requests.get(f"{BASE_URL}/admin/team-stats?period=today", headers=get_headers(admin_token))
                    if resp_after.status_code == 200:
                        data_after = resp_after.json()
                        admin_after = data_after.get('admin', {})
                        totals_after = data_after.get('totals', {})
                        print(f"  After admin: {admin_after}")
                        print(f"  After totals: {totals_after}")
                        
                        # Verify admin object
                        admin_checks = []
                        if admin_after.get('total_count') == admin_before.get('total_count', 0) + 1:
                            print(f"  ✓ admin.total_count increased by 1")
                            admin_checks.append(True)
                        else:
                            print(f"  ✗ admin.total_count = {admin_after.get('total_count')}, expected {admin_before.get('total_count', 0) + 1}")
                            admin_checks.append(False)
                        
                        if admin_after.get('revenue') == admin_before.get('revenue', 0) + 2000:
                            print(f"  ✓ admin.revenue increased by 2000")
                            admin_checks.append(True)
                        else:
                            print(f"  ✗ admin.revenue = {admin_after.get('revenue')}, expected {admin_before.get('revenue', 0) + 2000}")
                            admin_checks.append(False)
                        
                        if admin_after.get('profit') == admin_before.get('profit', 0) + 1500:
                            print(f"  ✓ admin.profit increased by 1500")
                            admin_checks.append(True)
                        else:
                            print(f"  ✗ admin.profit = {admin_after.get('profit')}, expected {admin_before.get('profit', 0) + 1500}")
                            admin_checks.append(False)
                        
                        # Verify totals include admin
                        totals_revenue_increase = totals_after.get('revenue', 0) - totals_before.get('revenue', 0)
                        totals_profit_increase = totals_after.get('profit', 0) - totals_before.get('profit', 0)
                        
                        if totals_revenue_increase == 2000:
                            print(f"  ✓ totals.revenue increased by 2000")
                            admin_checks.append(True)
                        else:
                            print(f"  ✗ totals.revenue increased by {totals_revenue_increase}, expected 2000")
                            admin_checks.append(False)
                        
                        if totals_profit_increase == 1500:
                            print(f"  ✓ totals.profit increased by 1500")
                            admin_checks.append(True)
                        else:
                            print(f"  ✗ totals.profit increased by {totals_profit_increase}, expected 1500")
                            admin_checks.append(False)
                        
                        if all(admin_checks):
                            print(f"✓ PASS: TEST (d)")
                            results["passed"] += 1
                            results["tests"].append({"test": "TEST (d)", "status": "PASS", "details": "Admin invoice increases admin object and totals correctly"})
                        else:
                            print(f"✗ FAIL: TEST (d)")
                            results["failed"] += 1
                            results["tests"].append({"test": "TEST (d)", "status": "FAIL", "details": "Admin object or totals mismatch"})
                    else:
                        print(f"  ✗ Failed to get stats after: {resp_after.status_code}")
                        results["failed"] += 1
                        results["tests"].append({"test": "TEST (d)", "status": "FAIL", "details": "Stats fetch failed"})
                else:
                    print(f"  ✗ Failed to create invoice: {resp_invoice.status_code} {resp_invoice.text}")
                    results["failed"] += 1
                    results["tests"].append({"test": "TEST (d)", "status": "FAIL", "details": "Invoice creation failed"})
            else:
                print(f"  ✗ Failed to get baseline stats: {resp_before.status_code}")
                results["failed"] += 1
                results["tests"].append({"test": "TEST (d)", "status": "FAIL", "details": "Baseline stats fetch failed"})
        print()
        
        # ========================================================================
        # TEST (e): emp1 GET /api/admin/team-stats → 403
        # ========================================================================
        print("TEST (e): emp1 GET /api/admin/team-stats → must be 403")
        print("-" * 80)
        resp = requests.get(f"{BASE_URL}/admin/team-stats", headers=get_headers(emp1_token))
        if resp.status_code == 403:
            print(f"✓ PASS: emp1 correctly blocked with 403")
            results["passed"] += 1
            results["tests"].append({"test": "TEST (e)", "status": "PASS", "details": "Non-admin correctly blocked"})
        else:
            print(f"✗ FAIL: Expected 403, got {resp.status_code}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST (e)", "status": "FAIL", "details": f"Got {resp.status_code} instead of 403"})
        print()
        
        # ========================================================================
        # TEST (f): Regression checks
        # ========================================================================
        print("TEST (f): Regression checks")
        print("-" * 80)
        
        # f.1: Rows still include all expected fields
        resp = requests.get(f"{BASE_URL}/admin/team-stats", headers=get_headers(admin_token))
        if resp.status_code == 200:
            data = resp.json()
            rows = data.get('rows', [])
            if rows:
                row = rows[0]
                required_fields = [
                    'calls', 'pct', 'attendance', 'check_in', 'check_out',
                    'customers_total', 'daily_goal', 'is_custom_goal',
                    'sales_count', 'invoices_count', 'total_count', 'revenue', 'profit'
                ]
                missing_fields = [f for f in required_fields if f not in row]
                if not missing_fields:
                    print(f"  ✓ Row includes all expected fields")
                    results["passed"] += 1
                    results["tests"].append({"test": "TEST (f.1)", "status": "PASS", "details": "All row fields present"})
                else:
                    print(f"  ✗ Row missing fields: {missing_fields}")
                    results["failed"] += 1
                    results["tests"].append({"test": "TEST (f.1)", "status": "FAIL", "details": f"Missing: {missing_fields}"})
            else:
                print(f"  ⚠ No rows returned (may be expected if no employees)")
                results["passed"] += 1
                results["tests"].append({"test": "TEST (f.1)", "status": "PASS", "details": "No rows (no employees)"})
        else:
            print(f"  ✗ Failed to get stats: {resp.status_code}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST (f.1)", "status": "FAIL", "details": f"API error: {resp.status_code}"})
        
        # f.2: Invalid period falls back to 'today'
        resp = requests.get(f"{BASE_URL}/admin/team-stats?period=xyz", headers=get_headers(admin_token))
        if resp.status_code == 200:
            data = resp.json()
            if data.get('period') == 'today':
                print(f"  ✓ Invalid period 'xyz' falls back to 'today'")
                results["passed"] += 1
                results["tests"].append({"test": "TEST (f.2)", "status": "PASS", "details": "Invalid period fallback working"})
            else:
                print(f"  ✗ Invalid period 'xyz' resulted in period='{data.get('period')}', expected 'today'")
                results["failed"] += 1
                results["tests"].append({"test": "TEST (f.2)", "status": "FAIL", "details": f"Period is '{data.get('period')}'"})
        else:
            print(f"  ✗ Failed to get stats: {resp.status_code}")
            results["failed"] += 1
            results["tests"].append({"test": "TEST (f.2)", "status": "FAIL", "details": f"API error: {resp.status_code}"})
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
            status_symbol = "✓" if test["status"] == "PASS" else "✗"
            print(f"{status_symbol} {test['test']}: {test['status']}")
            print(f"  {test['details']}")
        print("-" * 80)
    
    print("\n" + "="*80)
    if results["failed"] == 0:
        print("✓ ALL TESTS PASSED - TEAM-STATS ENDPOINT WORKING CORRECTLY")
    else:
        print(f"✗ {results['failed']} TEST(S) FAILED - REVIEW REQUIRED")
    print("="*80 + "\n")


if __name__ == "__main__":
    results = run_tests()
    print_summary(results)
    
    # Exit with appropriate code
    exit(0 if results["failed"] == 0 else 1)
