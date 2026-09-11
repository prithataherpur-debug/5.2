# Test Credentials — Pritha Cabinet CRM

## Admin
- username: `admin`
- password: `Admin@2026`

## Employees
- username: `emp1` .. `emp7` (all exist — fresh DB re-seeded on 2026-09-11 after environment reset)
- password: `Emp@2026`

Notes:
- Employee accounts are ADMIN-MANAGED (Team screen → Add / Remove).
- The backend seeds admin + emp1..emp7 ONLY on a completely fresh database (first boot). Deleted employees are NOT re-created on restart.
- ENVIRONMENT RESET on 2026-09-11 wiped the DB (fresh seed ran: admin + emp1..emp7 all present again) and removed both .env files + some pip packages — all restored (backend/.env with MONGO_URL/DB_NAME/JWT_SECRET/EMERGENT_LLM_KEY, frontend/.env with EXPO_PUBLIC_BACKEND_URL + EXPO_PACKAGER_* , pip: openpyxl, reportlab).
- DB_NAME=pritha_cabinet, MONGO_URL=mongodb://localhost:27017
