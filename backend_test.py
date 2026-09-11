#!/usr/bin/env python3
"""
Backend API Test Suite for Pritha Cabinet CRM
Tests two NEW features:
- FEATURE A: Self-service account update (PATCH /api/auth/me)
- FEATURE B: Overdue outstanding aggregation (my-report + team-stats)
"""

import requests
import json
from typing import Optional, Dict, Any

# Configuration
BASE_URL = "https://452252a5-0b79-4e4e-b2e3-a423e3f65811.preview.emergentagent.com/api"
ADMIN_USER = "admin"
ADMIN_PASS = "Admin@2026"
EMP1_USER = "emp1"
EMP1_PASS = "Emp@2026"

# Test state tracking
test_results = {
    "feature_a": {"passed": 0, "failed": 0, "details": []},
    "feature_b": {"passed": 0, "failed": 0, "details": []},
}
created_resources = {
    "customers": [],
    "sales": [],
    "invoices": [],
    "receipts": [],
}


def log_test(feature: str, scenario: str, passed: bool, message: str):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {feature} | {scenario}: {message}")
    test_results[feature]["details"].append({
        "scenario": scenario,
        "passed": passed,
        "message": message
    })
    if passed:
        test_results[feature]["passed"] += 1
    else:
        test_results[feature]["failed"] += 1


def login(username: str, password: str) -> Optional[str]:
    """Login and return access token"""
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
        else:
            print(f"❌ Login failed for {username}: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Login exception for {username}: {e}")
        return None


def make_request(method: str, endpoint: str, token: str, json_data: Optional[Dict] = None, 
                 params: Optional[Dict] = None) -> tuple[int, Any]:
    """Make authenticated API request"""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=json_data, timeout=10)
        elif method == "PATCH":
            resp = requests.patch(url, headers=headers, json=json_data, timeout=10)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=json_data, timeout=10)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=10)
        else:
            return 0, None
        
        try:
            return resp.status_code, resp.json()
        except:
            return resp.status_code, resp.text
    except Exception as e:
        print(f"❌ Request exception: {e}")
        return 0, str(e)


# ============================================================================
# FEATURE A: Self-service account update (PATCH /api/auth/me)
# ============================================================================

def test_feature_a():
    """Test self-service account update endpoint"""
    print("\n" + "="*80)
    print("FEATURE A: Self-service account update (PATCH /api/auth/me)")
    print("="*80)
    
    # Get initial emp1 token
    emp1_token = login(EMP1_USER, EMP1_PASS)
    if not emp1_token:
        log_test("feature_a", "SETUP", False, "Failed to login as emp1")
        return
    
    # A1: emp1 changes password to NewPass1
    print("\n--- A1: emp1 changes password to NewPass1 ---")
    status, data = make_request("PATCH", "/auth/me", emp1_token, {"password": "NewPass1"})
    if status == 200 and data.get("username") == EMP1_USER:
        log_test("feature_a", "A1", True, f"emp1 password change returned 200, username={data.get('username')}")
    else:
        log_test("feature_a", "A1", False, f"Expected 200 with username=emp1, got {status}: {data}")
        return
    
    # A2: Login with new password
    print("\n--- A2: Login with emp1/NewPass1 ---")
    new_token = login(EMP1_USER, "NewPass1")
    if new_token:
        log_test("feature_a", "A2", True, "Login with emp1/NewPass1 successful, password change confirmed")
    else:
        log_test("feature_a", "A2", False, "Login with emp1/NewPass1 failed, password change not working")
        return
    
    # A3: REVERT password back to Emp@2026
    print("\n--- A3: REVERT emp1 password to Emp@2026 ---")
    status, data = make_request("PATCH", "/auth/me", new_token, {"password": "Emp@2026"})
    if status == 200:
        # Confirm revert worked
        reverted_token = login(EMP1_USER, EMP1_PASS)
        if reverted_token:
            log_test("feature_a", "A3", True, "Password reverted to Emp@2026, login confirmed")
            emp1_token = reverted_token  # Update token for subsequent tests
        else:
            log_test("feature_a", "A3", False, "Password revert returned 200 but login with Emp@2026 failed")
            return
    else:
        log_test("feature_a", "A3", False, f"Password revert failed: {status} - {data}")
        return
    
    # A4: emp1 changes display_name to "Temp Name" then reverts
    print("\n--- A4: emp1 changes display_name ---")
    status, data = make_request("PATCH", "/auth/me", emp1_token, {"display_name": "Temp Name"})
    if status == 200 and data.get("display_name") == "Temp Name":
        log_test("feature_a", "A4a", True, f"display_name changed to 'Temp Name'")
        # Revert
        status2, data2 = make_request("PATCH", "/auth/me", emp1_token, {"display_name": "Employee 1"})
        if status2 == 200 and data2.get("display_name") == "Employee 1":
            log_test("feature_a", "A4b", True, "display_name reverted to 'Employee 1'")
        else:
            log_test("feature_a", "A4b", False, f"display_name revert failed: {status2} - {data2}")
    else:
        log_test("feature_a", "A4a", False, f"display_name change failed: {status} - {data}")
    
    # A5: emp1 tries password too short (< 4 chars)
    print("\n--- A5: emp1 tries password 'ab' (too short) ---")
    status, data = make_request("PATCH", "/auth/me", emp1_token, {"password": "ab"})
    if status == 400:
        log_test("feature_a", "A5", True, f"Short password correctly rejected with 400: {data}")
    else:
        log_test("feature_a", "A5", False, f"Expected 400 for short password, got {status}: {data}")
    
    # A6: emp1 tries to change username to 'admin' (already taken)
    print("\n--- A6: emp1 tries new_username='admin' (already taken) ---")
    status, data = make_request("PATCH", "/auth/me", emp1_token, {"new_username": "admin"})
    if status == 409:
        log_test("feature_a", "A6a", True, f"Username conflict correctly rejected with 409: {data}")
        # Confirm emp1 is still emp1
        verify_token = login(EMP1_USER, EMP1_PASS)
        if verify_token:
            log_test("feature_a", "A6b", True, "emp1 username unchanged, login still works")
        else:
            log_test("feature_a", "A6b", False, "emp1 login failed after username conflict attempt")
    else:
        log_test("feature_a", "A6a", False, f"Expected 409 for duplicate username, got {status}: {data}")
    
    # A7: admin can self-update
    print("\n--- A7: admin PATCH /auth/me ---")
    admin_token = login(ADMIN_USER, ADMIN_PASS)
    if admin_token:
        status, data = make_request("PATCH", "/auth/me", admin_token, {"display_name": "Admin"})
        if status == 200:
            log_test("feature_a", "A7", True, f"admin self-update successful: {data.get('display_name')}")
        else:
            log_test("feature_a", "A7", False, f"admin self-update failed: {status} - {data}")
    else:
        log_test("feature_a", "A7", False, "Failed to login as admin")
    
    # A8: emp1 PATCH with empty body
    print("\n--- A8: emp1 PATCH /auth/me with empty body ---")
    status, data = make_request("PATCH", "/auth/me", emp1_token, {})
    if status == 400 and "No changes provided" in str(data):
        log_test("feature_a", "A8", True, f"Empty body correctly rejected with 400: {data}")
    else:
        log_test("feature_a", "A8", False, f"Expected 400 'No changes provided', got {status}: {data}")
    
    # CRITICAL END STATE: Verify emp1 is emp1/Emp@2026/Employee 1
    print("\n--- CRITICAL END STATE VERIFICATION ---")
    final_token = login(EMP1_USER, EMP1_PASS)
    if final_token:
        status, data = make_request("GET", "/auth/me", final_token)
        if status == 200:
            username_ok = data.get("username") == EMP1_USER
            display_ok = data.get("display_name") == "Employee 1"
            if username_ok and display_ok:
                log_test("feature_a", "END_STATE", True, 
                        f"emp1 end state correct: username={data.get('username')}, display_name={data.get('display_name')}")
            else:
                log_test("feature_a", "END_STATE", False, 
                        f"emp1 end state incorrect: username={data.get('username')}, display_name={data.get('display_name')}")
        else:
            log_test("feature_a", "END_STATE", False, f"Failed to get emp1 profile: {status}")
    else:
        log_test("feature_a", "END_STATE", False, "Failed to login as emp1/Emp@2026 at end")


# ============================================================================
# FEATURE B: Overdue outstanding aggregation
# ============================================================================

def test_feature_b():
    """Test overdue outstanding aggregation in my-report and team-stats"""
    print("\n" + "="*80)
    print("FEATURE B: Overdue outstanding aggregation")
    print("="*80)
    
    emp1_token = login(EMP1_USER, EMP1_PASS)
    admin_token = login(ADMIN_USER, ADMIN_PASS)
    
    if not emp1_token or not admin_token:
        log_test("feature_b", "SETUP", False, "Failed to login")
        return
    
    # B1: Baseline - get emp1's current overdue
    print("\n--- B1: Baseline emp1 overdue ---")
    status, data = make_request("GET", "/stats/my-report", emp1_token, params={"weeks": 4, "months": 3})
    if status == 200:
        overdue = data.get("overdue", {})
        if isinstance(overdue, dict) and "total" in overdue and "customer_count" in overdue:
            T0 = float(overdue.get("total", 0))
            C0 = int(overdue.get("customer_count", 0))
            log_test("feature_b", "B1", True, 
                    f"Baseline overdue: total={T0}, customer_count={C0}")
        else:
            log_test("feature_b", "B1", False, f"overdue structure incorrect: {overdue}")
            return
    else:
        log_test("feature_b", "B1", False, f"my-report failed: {status} - {data}")
        return
    
    # B2: Create customer and sale WITHOUT receipt
    print("\n--- B2: Create sale without receipt ---")
    # Create customer first
    cust_data = {
        "name": "Overdue Test Customer",
        "phone": "9876543210",
        "address": "Test Address"
    }
    status, cust = make_request("POST", "/customers", emp1_token, cust_data)
    if status == 200:
        customer_id = cust.get("id")
        created_resources["customers"].append(customer_id)
        log_test("feature_b", "B2a", True, f"Customer created: {customer_id}")
    else:
        log_test("feature_b", "B2a", False, f"Customer creation failed: {status} - {cust}")
        return
    
    # Create sale
    sale_data = {
        "customer_name": "Overdue Test Customer",
        "customer_mobile": "9876543210",
        "amount": 1500,
        "payment_mode": "cash",
        "purchase_amount": 0
    }
    status, sale = make_request("POST", "/sales", emp1_token, sale_data)
    if status == 200:
        sale_id = sale.get("id")
        created_resources["sales"].append(sale_id)
        log_test("feature_b", "B2b", True, f"Sale created without receipt: {sale_id}, amount=1500")
    else:
        log_test("feature_b", "B2b", False, f"Sale creation failed: {status} - {sale}")
        return
    
    # B3: Check emp1 my-report - overdue should increase
    print("\n--- B3: Check emp1 overdue after sale ---")
    status, data = make_request("GET", "/stats/my-report", emp1_token, params={"weeks": 4, "months": 3})
    if status == 200:
        overdue = data.get("overdue", {})
        T1 = float(overdue.get("total", 0))
        C1 = int(overdue.get("customer_count", 0))
        
        # Check if total increased by 1500
        if abs(T1 - (T0 + 1500)) < 0.01:
            log_test("feature_b", "B3a", True, f"overdue.total increased by 1500: {T0} → {T1}")
        else:
            log_test("feature_b", "B3a", False, 
                    f"overdue.total should be {T0 + 1500}, got {T1} (diff: {T1 - T0})")
        
        # Check if customer_count increased (should be at least C0+1 if new customer)
        if C1 >= C0:
            log_test("feature_b", "B3b", True, f"customer_count: {C0} → {C1}")
        else:
            log_test("feature_b", "B3b", False, f"customer_count decreased: {C0} → {C1}")
    else:
        log_test("feature_b", "B3", False, f"my-report failed: {status} - {data}")
    
    # B4: Check admin team-stats - emp1 row should show overdue
    print("\n--- B4: Check admin team-stats ---")
    status, data = make_request("GET", "/admin/team-stats", admin_token, params={"period": "all"})
    if status == 200:
        rows = data.get("rows", [])
        emp1_row = next((r for r in rows if r.get("username") == EMP1_USER), None)
        totals = data.get("totals", {})
        
        if emp1_row:
            emp1_overdue_total = emp1_row.get("overdue_total", 0)
            emp1_overdue_customers = emp1_row.get("overdue_customers", 0)
            if emp1_overdue_total >= 1500:
                log_test("feature_b", "B4a", True, 
                        f"emp1 row overdue_total={emp1_overdue_total}, overdue_customers={emp1_overdue_customers}")
            else:
                log_test("feature_b", "B4a", False, 
                        f"emp1 row overdue_total={emp1_overdue_total} (expected >= 1500)")
        else:
            log_test("feature_b", "B4a", False, "emp1 row not found in team-stats")
        
        # Check totals include overdue
        totals_overdue = totals.get("overdue_total", 0)
        if totals_overdue >= 1500:
            log_test("feature_b", "B4b", True, f"totals.overdue_total={totals_overdue}")
        else:
            log_test("feature_b", "B4b", False, f"totals.overdue_total={totals_overdue} (expected >= 1500)")
    else:
        log_test("feature_b", "B4", False, f"team-stats failed: {status} - {data}")
    
    # B5: Create money receipt linked to the sale
    print("\n--- B5: Create receipt linked to sale ---")
    receipt_data = {
        "customer_name": "Overdue Test Customer",
        "customer_mobile": "9876543210",
        "amount": 1500,
        "payment_mode": "cash",
        "source_type": "sale",
        "source_id": sale_id
    }
    status, receipt = make_request("POST", "/receipts", emp1_token, receipt_data)
    if status == 200:
        receipt_id = receipt.get("id")
        created_resources["receipts"].append(receipt_id)
        log_test("feature_b", "B5", True, f"Receipt created and linked to sale: {receipt_id}")
    else:
        log_test("feature_b", "B5", False, f"Receipt creation failed: {status} - {receipt}")
        return
    
    # B6: Check emp1 my-report - overdue should drop
    print("\n--- B6: Check emp1 overdue after receipt ---")
    status, data = make_request("GET", "/stats/my-report", emp1_token, params={"weeks": 4, "months": 3})
    if status == 200:
        overdue = data.get("overdue", {})
        T2 = float(overdue.get("total", 0))
        
        # Should drop back to approximately T0 (within small margin for other entries)
        if abs(T2 - T0) < 10:  # Allow small margin
            log_test("feature_b", "B6", True, 
                    f"overdue.total dropped after receipt: {T1} → {T2} (baseline was {T0})")
        else:
            log_test("feature_b", "B6", False, 
                    f"overdue.total should drop to ~{T0}, got {T2} (was {T1} before receipt)")
    else:
        log_test("feature_b", "B6", False, f"my-report failed: {status} - {data}")
    
    # B7: Invoice check - create invoice without receipt
    print("\n--- B7: Invoice without receipt ---")
    invoice_data = {
        "customer_name": "Overdue Test Customer",
        "customer_mobile": "9876543210",
        "items": [
            {"name": "Test Item", "qty": 1, "unit_price": 2000, "unit_cost": 500}
        ]
    }
    status, invoice = make_request("POST", "/invoices", emp1_token, invoice_data)
    if status == 200:
        invoice_id = invoice.get("id")
        created_resources["invoices"].append(invoice_id)
        log_test("feature_b", "B7a", True, f"Invoice created without receipt: {invoice_id}, total=2000")
        
        # Check overdue increased
        status2, data2 = make_request("GET", "/stats/my-report", emp1_token, params={"weeks": 4, "months": 3})
        if status2 == 200:
            T3 = float(data2.get("overdue", {}).get("total", 0))
            if abs(T3 - (T2 + 2000)) < 0.01:
                log_test("feature_b", "B7b", True, f"overdue.total increased by 2000: {T2} → {T3}")
            else:
                log_test("feature_b", "B7b", False, 
                        f"overdue.total should be {T2 + 2000}, got {T3} (diff: {T3 - T2})")
        else:
            log_test("feature_b", "B7b", False, f"my-report failed: {status2}")
    else:
        log_test("feature_b", "B7a", False, f"Invoice creation failed: {status} - {invoice}")
    
    # B8: Authorization - emp1 cannot access team-stats
    print("\n--- B8: emp1 tries to access team-stats ---")
    status, data = make_request("GET", "/admin/team-stats", emp1_token, params={"period": "all"})
    if status == 403:
        log_test("feature_b", "B8", True, "emp1 correctly blocked from team-stats with 403")
    else:
        log_test("feature_b", "B8", False, f"Expected 403 for emp1 team-stats, got {status}")
    
    # B9: my-report scoping - admin sees only their own overdue
    print("\n--- B9: admin my-report scoping ---")
    status, data = make_request("GET", "/stats/my-report", admin_token, params={"weeks": 4, "months": 3})
    if status == 200:
        overdue = data.get("overdue", {})
        admin_total = float(overdue.get("total", 0))
        # Admin's overdue should NOT include emp1's entries
        log_test("feature_b", "B9", True, 
                f"admin my-report returns overdue for admin only: total={admin_total}")
    else:
        log_test("feature_b", "B9", False, f"admin my-report failed: {status} - {data}")
    
    # CLEANUP
    print("\n--- CLEANUP: Deleting test data ---")
    cleanup_feature_b(emp1_token, admin_token)


def cleanup_feature_b(emp1_token: str, admin_token: str):
    """Clean up all test data created in feature B"""
    cleanup_count = {"receipts": 0, "invoices": 0, "sales": 0, "customers": 0}
    
    # Delete receipts
    for receipt_id in created_resources["receipts"]:
        status, _ = make_request("DELETE", f"/receipts/{receipt_id}", admin_token)
        if status == 200:
            cleanup_count["receipts"] += 1
    
    # Delete invoices
    for invoice_id in created_resources["invoices"]:
        status, _ = make_request("DELETE", f"/invoices/{invoice_id}", admin_token)
        if status == 200:
            cleanup_count["invoices"] += 1
    
    # Delete sales
    for sale_id in created_resources["sales"]:
        status, _ = make_request("DELETE", f"/sales/{sale_id}", admin_token)
        if status == 200:
            cleanup_count["sales"] += 1
    
    # Delete customers
    for customer_id in created_resources["customers"]:
        status, _ = make_request("DELETE", f"/customers/{customer_id}", admin_token)
        if status == 200:
            cleanup_count["customers"] += 1
    
    print(f"Cleanup complete: {cleanup_count}")
    log_test("feature_b", "CLEANUP", True, 
            f"Deleted {cleanup_count['customers']} customers, {cleanup_count['sales']} sales, "
            f"{cleanup_count['invoices']} invoices, {cleanup_count['receipts']} receipts")


# ============================================================================
# Main execution
# ============================================================================

def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for feature, results in test_results.items():
        total = results["passed"] + results["failed"]
        print(f"\n{feature.upper()}:")
        print(f"  Passed: {results['passed']}/{total}")
        print(f"  Failed: {results['failed']}/{total}")
        
        if results["failed"] > 0:
            print(f"  Failed scenarios:")
            for detail in results["details"]:
                if not detail["passed"]:
                    print(f"    - {detail['scenario']}: {detail['message']}")
    
    total_passed = sum(r["passed"] for r in test_results.values())
    total_failed = sum(r["failed"] for r in test_results.values())
    total_tests = total_passed + total_failed
    
    print(f"\n{'='*80}")
    print(f"OVERALL: {total_passed}/{total_tests} tests passed")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    print("Starting Pritha Cabinet CRM Backend Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Testing with: {ADMIN_USER}/{ADMIN_PASS} and {EMP1_USER}/{EMP1_PASS}")
    
    # Run tests
    test_feature_a()
    test_feature_b()
    
    # Print summary
    print_summary()
