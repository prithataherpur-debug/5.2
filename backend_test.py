#!/usr/bin/env python3
"""
Backend test for employee seeding verification.
Tests that only admin + emp1 exist after the seed change (range(1,8) → range(1,2)).
"""
import requests
import sys

BASE_URL = "https://f88dd101-329c-4578-96fc-edb74cff4162.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_USER = "admin"
ADMIN_PASS = "Admin@2026"
EMP1_USER = "emp1"
EMP1_PASS = "Emp@2026"
EMP2_USER = "emp2"
EMP2_PASS = "Emp@2026"

def test_admin_login():
    """Test 1: Admin login should succeed with 200 + access_token"""
    print("\n[TEST 1] Admin login (admin/Admin@2026)...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    }, timeout=10)
    
    if resp.status_code != 200:
        print(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
        print(f"  Response: {resp.text}")
        return None
    
    data = resp.json()
    if "access_token" not in data:
        print(f"  ❌ FAILED: No access_token in response")
        print(f"  Response: {data}")
        return None
    
    print(f"  ✅ PASSED: Admin login successful, got access_token")
    return data["access_token"]


def test_emp1_login():
    """Test 2: emp1 login should succeed with 200 + access_token"""
    print("\n[TEST 2] emp1 login (emp1/Emp@2026)...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": EMP1_USER,
        "password": EMP1_PASS
    }, timeout=10)
    
    if resp.status_code != 200:
        print(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
        print(f"  Response: {resp.text}")
        return None
    
    data = resp.json()
    if "access_token" not in data:
        print(f"  ❌ FAILED: No access_token in response")
        print(f"  Response: {data}")
        return None
    
    print(f"  ✅ PASSED: emp1 login successful, got access_token")
    return data["access_token"]


def test_emp2_login():
    """Test 3: emp2 login should fail with 401 (user should NOT exist)"""
    print("\n[TEST 3] emp2 login (emp2/Emp@2026) - should fail with 401...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": EMP2_USER,
        "password": EMP2_PASS
    }, timeout=10)
    
    if resp.status_code == 401:
        print(f"  ✅ PASSED: emp2 login correctly rejected with 401 (user does not exist)")
        return True
    else:
        print(f"  ❌ FAILED: Expected 401, got {resp.status_code}")
        print(f"  Response: {resp.text}")
        return False


def test_list_users(admin_token):
    """Test 4: GET /api/admin/users should return exactly ['admin', 'emp1']"""
    print("\n[TEST 4] GET /api/admin/users - should return exactly 2 users (admin, emp1)...")
    resp = requests.get(f"{BASE_URL}/admin/users", 
                       headers={"Authorization": f"Bearer {admin_token}"},
                       timeout=10)
    
    if resp.status_code != 200:
        print(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
        print(f"  Response: {resp.text}")
        return False
    
    users = resp.json()
    if not isinstance(users, list):
        print(f"  ❌ FAILED: Response is not a list")
        print(f"  Response: {users}")
        return False
    
    usernames = [u["username"] for u in users]
    expected = ["admin", "emp1"]
    
    if len(usernames) != 2:
        print(f"  ❌ FAILED: Expected exactly 2 users, got {len(usernames)}")
        print(f"  Users: {usernames}")
        return False
    
    if set(usernames) != set(expected):
        print(f"  ❌ FAILED: Expected users {expected}, got {usernames}")
        return False
    
    print(f"  ✅ PASSED: Exactly 2 users exist: {usernames}")
    return True


def test_regression_smoke(admin_token):
    """Test 5: Regression smoke tests - various endpoints should return 200"""
    print("\n[TEST 5] Regression smoke tests...")
    
    tests = [
        ("GET /api/stats/today", f"{BASE_URL}/stats/today"),
        ("GET /api/sales", f"{BASE_URL}/sales?scope=all"),
        ("GET /api/customers/search?q=test", f"{BASE_URL}/customers/search?q=test"),
        ("GET /api/deliveries", f"{BASE_URL}/deliveries"),
    ]
    
    all_passed = True
    for name, url in tests:
        print(f"  Testing {name}...")
        resp = requests.get(url, 
                           headers={"Authorization": f"Bearer {admin_token}"},
                           timeout=10)
        if resp.status_code == 200:
            print(f"    ✅ {name} returned 200")
        else:
            print(f"    ❌ {name} returned {resp.status_code}")
            print(f"    Response: {resp.text[:200]}")
            all_passed = False
    
    if all_passed:
        print(f"  ✅ PASSED: All regression smoke tests returned 200")
    else:
        print(f"  ❌ FAILED: Some regression tests failed")
    
    return all_passed


def test_admin_add_delete_employee(admin_token):
    """Test 6: Verify admin can ADD, login, and DELETE an employee"""
    print("\n[TEST 6] Admin add/delete employee flow...")
    
    # Step 1: Create temporary employee
    print("  Step 1: Creating temporary employee 'tmpseed1'...")
    resp = requests.post(f"{BASE_URL}/admin/users",
                        headers={"Authorization": f"Bearer {admin_token}"},
                        json={
                            "username": "tmpseed1",
                            "password": "Tmp@12345",
                            "display_name": "Tmp Seed"
                        },
                        timeout=10)
    
    if resp.status_code != 200:
        print(f"    ❌ FAILED: Could not create user, got {resp.status_code}")
        print(f"    Response: {resp.text}")
        return False
    
    created_user = resp.json()
    print(f"    ✅ Created user: {created_user.get('username')}")
    
    # Step 2: Verify user appears in list
    print("  Step 2: Verifying user appears in GET /api/admin/users...")
    resp = requests.get(f"{BASE_URL}/admin/users",
                       headers={"Authorization": f"Bearer {admin_token}"},
                       timeout=10)
    
    if resp.status_code != 200:
        print(f"    ❌ FAILED: Could not list users, got {resp.status_code}")
        return False
    
    users = resp.json()
    usernames = [u["username"] for u in users]
    
    if "tmpseed1" not in usernames:
        print(f"    ❌ FAILED: tmpseed1 not found in user list: {usernames}")
        return False
    
    if len(usernames) != 3:  # admin, emp1, tmpseed1
        print(f"    ❌ FAILED: Expected 3 users, got {len(usernames)}: {usernames}")
        return False
    
    print(f"    ✅ User list now contains 3 users: {usernames}")
    
    # Step 3: Verify new user can login
    print("  Step 3: Verifying tmpseed1 can login...")
    resp = requests.post(f"{BASE_URL}/auth/login",
                        json={
                            "username": "tmpseed1",
                            "password": "Tmp@12345"
                        },
                        timeout=10)
    
    if resp.status_code != 200:
        print(f"    ❌ FAILED: tmpseed1 login failed with {resp.status_code}")
        print(f"    Response: {resp.text}")
        return False
    
    data = resp.json()
    if "access_token" not in data:
        print(f"    ❌ FAILED: No access_token in login response")
        return False
    
    print(f"    ✅ tmpseed1 login successful")
    
    # Step 4: Delete the user
    print("  Step 4: Deleting tmpseed1...")
    resp = requests.delete(f"{BASE_URL}/admin/users/tmpseed1",
                          headers={"Authorization": f"Bearer {admin_token}"},
                          timeout=10)
    
    if resp.status_code != 200:
        print(f"    ❌ FAILED: Could not delete user, got {resp.status_code}")
        print(f"    Response: {resp.text}")
        return False
    
    print(f"    ✅ User deleted successfully")
    
    # Step 5: Verify user is gone from list
    print("  Step 5: Verifying user is removed from list...")
    resp = requests.get(f"{BASE_URL}/admin/users",
                       headers={"Authorization": f"Bearer {admin_token}"},
                       timeout=10)
    
    if resp.status_code != 200:
        print(f"    ❌ FAILED: Could not list users, got {resp.status_code}")
        return False
    
    users = resp.json()
    usernames = [u["username"] for u in users]
    
    if "tmpseed1" in usernames:
        print(f"    ❌ FAILED: tmpseed1 still in user list: {usernames}")
        return False
    
    if len(usernames) != 2:  # back to admin, emp1
        print(f"    ❌ FAILED: Expected 2 users after delete, got {len(usernames)}: {usernames}")
        return False
    
    print(f"    ✅ User list back to 2 users: {usernames}")
    
    print(f"  ✅ PASSED: Full add/login/delete flow working correctly")
    return True


def main():
    print("=" * 80)
    print("BACKEND TEST: Employee Seeding Verification")
    print("Testing that only admin + emp1 exist after seed change (range(1,8) → range(1,2))")
    print("=" * 80)
    
    results = []
    
    # Test 1: Admin login
    admin_token = test_admin_login()
    results.append(("Admin login", admin_token is not None))
    
    if not admin_token:
        print("\n❌ CRITICAL: Admin login failed, cannot continue tests")
        sys.exit(1)
    
    # Test 2: emp1 login
    emp1_token = test_emp1_login()
    results.append(("emp1 login", emp1_token is not None))
    
    # Test 3: emp2 login should fail
    emp2_result = test_emp2_login()
    results.append(("emp2 login rejection", emp2_result))
    
    # Test 4: List users
    list_result = test_list_users(admin_token)
    results.append(("List users (exactly 2)", list_result))
    
    # Test 5: Regression smoke
    smoke_result = test_regression_smoke(admin_token)
    results.append(("Regression smoke tests", smoke_result))
    
    # Test 6: Admin add/delete employee
    add_delete_result = test_admin_add_delete_employee(admin_token)
    results.append(("Admin add/delete employee", add_delete_result))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Employee seeding working correctly!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
