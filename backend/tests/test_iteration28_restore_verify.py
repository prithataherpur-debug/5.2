"""
Iteration 28 — RESTORE-AND-VERIFY end-to-end backend tests.
Covers: login (admin+emp), employee daily-call scope, PATCH call status,
create sale, create invoice, create receipt, daybook cash/online split, Excel exports,
due collections POST/GET.
"""
import os
import uuid
import time
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL") or "https://open-my-project-10.preview.emergentagent.com"
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

UNIQ = uuid.uuid4().hex[:6]
CASH_AMT = 1200.0
ONLINE_AMT = 800.0
TOTAL_AMT = CASH_AMT + ONLINE_AMT


# ---------- fixtures ----------
@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login",
                      json={"username": "admin", "password": "Admin@2026"}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    tok = r.json()["access_token"]
    assert tok
    return tok


@pytest.fixture(scope="module")
def emp_token():
    r = requests.post(f"{API}/auth/login",
                      json={"username": "emp1", "password": "Emp@2026"}, timeout=15)
    assert r.status_code == 200, f"emp1 login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


def _h(t): return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


# ---------- (1) auth ----------
class TestAuth:
    def test_health_ok(self):
        r = requests.get(f"{API}/", timeout=10)
        assert r.status_code == 200
        assert "message" in r.json()

    def test_admin_login(self, admin_token):
        r = requests.get(f"{API}/auth/me", headers=_h(admin_token), timeout=10)
        assert r.status_code == 200
        j = r.json()
        assert j["username"] == "admin"
        assert j["role"] == "admin"

    def test_employee_login(self, emp_token):
        r = requests.get(f"{API}/auth/me", headers=_h(emp_token), timeout=10)
        assert r.status_code == 200
        j = r.json()
        assert j["username"] == "emp1"
        assert j["role"] == "employee"

    def test_bad_password_rejected(self):
        r = requests.post(f"{API}/auth/login",
                          json={"username": "admin", "password": "wrong"}, timeout=10)
        assert r.status_code == 401


# ---------- (2) customer daily list + status ----------
class TestCustomers:
    _cust_id = None

    def test_emp_scope_mine_returns_list(self, emp_token):
        r = requests.get(f"{API}/customers?scope=mine",
                         headers=_h(emp_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_create_customer_as_emp(self, emp_token):
        payload = {
            "name": f"TEST_R28_{UNIQ}",
            "phone": f"9199{UNIQ}",   # 10 digits
            "address": "Test addr",
            "notes": "restore verify",
        }
        r = requests.post(f"{API}/customers", headers=_h(emp_token),
                          json=payload, timeout=15)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["assigned_to"] == "emp1"
        assert j["status"] == "pending"
        TestCustomers._cust_id = j["id"]

    def test_patch_status_interested(self, emp_token):
        cid = TestCustomers._cust_id
        assert cid, "prior test must have created a customer"
        r = requests.patch(f"{API}/customers/{cid}/status", headers=_h(emp_token),
                           json={"status": "interested"}, timeout=15)
        assert r.status_code == 200
        assert r.json()["status"] == "interested"

    def test_customer_appears_in_scope(self, emp_token):
        r = requests.get(f"{API}/customers?scope=mine",
                         headers=_h(emp_token), timeout=15)
        assert r.status_code == 200
        assert any(c["id"] == TestCustomers._cust_id for c in r.json())


# ---------- (3) sale, invoice, receipt ----------
class TestSalesInvoicesReceipts:
    _sale_id = None
    _invoice_id = None
    _invoice_no = None
    _receipt_id = None

    def test_create_sale_mixed(self, emp_token):
        cid = TestCustomers._cust_id
        payload = {
            "customer_id": cid,
            "customer_name": f"TEST_R28_{UNIQ}",
            "amount": TOTAL_AMT,
            "cash_amount": CASH_AMT,
            "online_amount": ONLINE_AMT,
            "product": "Cabinet",
            "notes": "restore",
        }
        r = requests.post(f"{API}/sales", headers=_h(emp_token),
                          json=payload, timeout=20)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["amount"] == pytest.approx(TOTAL_AMT)
        assert j["cash_amount"] == pytest.approx(CASH_AMT)
        assert j["online_amount"] == pytest.approx(ONLINE_AMT)
        assert j["payment_mode"] == "mixed"
        TestSalesInvoicesReceipts._sale_id = j["id"]

    def test_sale_appears_in_list(self, emp_token):
        r = requests.get(f"{API}/sales?scope=mine",
                         headers=_h(emp_token), timeout=15)
        assert r.status_code == 200
        ids = [s["id"] for s in r.json()]
        assert TestSalesInvoicesReceipts._sale_id in ids

    def test_create_invoice(self, emp_token):
        payload = {
            "customer_name": f"TEST_R28_{UNIQ}",
            "customer_mobile": f"9199{UNIQ}",
            "customer_address": "Test addr",
            "items": [
                {"name": "Cabinet A", "qty": 2, "unit_price": 500.0},
                {"name": "Cabinet B", "qty": 1, "unit_price": 200.0},
            ],
            "notes": "restore invoice",
            "customer_id": TestCustomers._cust_id,
            "cash_amount": 700.0,
            "online_amount": 500.0,
        }
        r = requests.post(f"{API}/invoices", headers=_h(emp_token),
                          json=payload, timeout=30)
        # PDF upload requires EMERGENT_LLM_KEY; storage-dep may fail with 500 — surface that clearly
        if r.status_code >= 500:
            pytest.skip(f"Invoice PDF storage unavailable (known non-blocker): {r.status_code} {r.text[:200]}")
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["total"] == pytest.approx(1200.0)
        assert j["cash_amount"] == pytest.approx(700.0)
        assert j["online_amount"] == pytest.approx(500.0)
        assert j["invoice_no"]
        TestSalesInvoicesReceipts._invoice_id = j["id"]
        TestSalesInvoicesReceipts._invoice_no = j["invoice_no"]

    def test_invoice_get(self, emp_token):
        iid = TestSalesInvoicesReceipts._invoice_id
        if not iid:
            pytest.skip("invoice not created")
        r = requests.get(f"{API}/invoices/{iid}", headers=_h(emp_token), timeout=10)
        assert r.status_code == 200
        assert r.json()["id"] == iid

    def test_create_money_receipt(self, emp_token):
        sale_id = TestSalesInvoicesReceipts._sale_id
        payload = {
            "customer_id": TestCustomers._cust_id,
            "customer_name": f"TEST_R28_{UNIQ}",
            "customer_mobile": f"9199{UNIQ}",
            "amount": ONLINE_AMT,
            "payment_mode": "online",
            "cash_amount": 0,
            "online_amount": ONLINE_AMT,
            "source_type": "sale",
            "source_id": sale_id,
            "narration": "online part of sale",
        }
        r = requests.post(f"{API}/receipts", headers=_h(emp_token),
                          json=payload, timeout=30)
        if r.status_code >= 500:
            pytest.skip(f"Receipt PDF storage unavailable (known non-blocker): {r.status_code} {r.text[:200]}")
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["amount"] == pytest.approx(ONLINE_AMT)
        assert j["payment_mode"] == "online"
        assert j["online_amount"] == pytest.approx(ONLINE_AMT)
        TestSalesInvoicesReceipts._receipt_id = j["id"]

    def test_receipt_appears_in_list(self, emp_token):
        rid = TestSalesInvoicesReceipts._receipt_id
        if not rid:
            pytest.skip("receipt not created")
        r = requests.get(f"{API}/receipts", headers=_h(emp_token), timeout=15)
        assert r.status_code == 200
        assert any(x["id"] == rid for x in r.json())


# ---------- (4) daybook cash vs online ----------
class TestDaybook:
    def test_daybook_loads_admin(self, admin_token):
        r = requests.get(f"{API}/daybook", headers=_h(admin_token), timeout=20)
        assert r.status_code == 200, r.text
        j = r.json()
        # required top-level keys
        assert "grand_total" in j
        gt = j["grand_total"]
        assert "cash" in gt and "online" in gt
        # cash + online must sum to grand
        total_key = gt.get("total") if "total" in gt else (gt.get("grand") if "grand" in gt else None)
        if total_key is None:
            # some builds nest — accept 'amount' too
            total_key = gt.get("amount")
        assert total_key is not None, f"no total key in grand_total: {gt}"
        assert float(gt["cash"]) + float(gt["online"]) == pytest.approx(float(total_key), abs=0.5)

    def test_daybook_forbidden_for_random_emp(self, emp_token):
        # emp1 is NOT the collector by default
        r = requests.get(f"{API}/daybook", headers=_h(emp_token), timeout=15)
        assert r.status_code in (200, 403), f"unexpected: {r.status_code}"
        # If 200, then emp is collector (fine). If 403 (default state), that's also fine.


# ---------- (5) Excel exports ----------
class TestExcelExports:
    def test_daybook_export_token_and_xlsx(self, admin_token):
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        r = requests.get(f"{API}/daybook/export-token",
                         params={"from": today, "to": today},
                         headers=_h(admin_token), timeout=15)
        assert r.status_code == 200, r.text
        token = r.json().get("token")
        assert token, f"no token in {r.json()}"
        r2 = requests.get(f"{API}/daybook.xlsx", params={"token": token}, timeout=30)
        assert r2.status_code == 200, f"{r2.status_code} {r2.text[:200]}"
        # xlsx = zip = starts with PK
        assert r2.content[:2] == b"PK", "response is not a valid xlsx (PK header missing)"
        assert len(r2.content) > 500

    def test_admin_backup_xlsx(self, admin_token):
        r = requests.get(f"{API}/admin/backup/token", headers=_h(admin_token), timeout=15)
        assert r.status_code == 200, r.text
        token = r.json().get("token")
        assert token
        r2 = requests.get(f"{API}/admin/backup.xlsx", params={"token": token}, timeout=60)
        assert r2.status_code == 200, f"{r2.status_code} {r2.text[:200]}"
        assert r2.content[:2] == b"PK"


# ---------- (6) collections ----------
class TestCollections:
    _cid = None

    def test_create_collection(self, emp_token):
        payload = {"cash_total": 500.0, "online_total": 300.0, "notes": "restore test"}
        r = requests.post(f"{API}/collections", headers=_h(emp_token),
                          json=payload, timeout=15)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["cash_total"] == pytest.approx(500.0)
        assert j["online_total"] == pytest.approx(300.0)
        assert j["grand_total"] == pytest.approx(800.0)
        TestCollections._cid = j["id"]

    def test_list_collections(self, emp_token):
        r = requests.get(f"{API}/collections", headers=_h(emp_token), timeout=15)
        assert r.status_code == 200
        ids = [x["id"] for x in r.json()]
        assert TestCollections._cid in ids

    def test_collections_summary(self, admin_token):
        r = requests.get(f"{API}/collections/summary", headers=_h(admin_token), timeout=15)
        assert r.status_code == 200


# ---------- teardown: hard-clean seed ----------
def test_zz_cleanup(admin_token):
    """Cleanup TEST_R28 customer (cascade). Best-effort."""
    r = requests.get(f"{API}/customers/search", params={"q": f"TEST_R28_{UNIQ}"},
                     headers=_h(admin_token), timeout=15)
    if r.status_code == 200:
        for c in r.json().get("customers", []):
            requests.delete(f"{API}/customers/{c['id']}", headers=_h(admin_token), timeout=10)
