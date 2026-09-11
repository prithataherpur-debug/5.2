# Test Credentials — Pritha Cabinet CRM

## Admin
- username: `admin`
- password: `Admin@2026`

## Employee
- username: `emp1`
- password: `Emp@2026`

Notes:
- ONLY admin + emp1 exist. Per owner request (2026-09-11): fresh-install seed now creates ONLY 1 employee (emp1) — if more employees are needed, the admin adds them via Team screen → Add (POST /api/admin/users).
- Employee accounts are ADMIN-MANAGED. Deleted employees are NOT re-created on restart.
- ENVIRONMENT RESET on 2026-09-11 wiped the DB + both .env files + some pip packages — all restored (backend/.env with MONGO_URL/DB_NAME/JWT_SECRET/EMERGENT_LLM_KEY, frontend/.env with EXPO_PUBLIC_BACKEND_URL + EXPO_PACKAGER_*, pip: openpyxl, reportlab).
- DB_NAME=pritha_cabinet, MONGO_URL=mongodb://localhost:27017
