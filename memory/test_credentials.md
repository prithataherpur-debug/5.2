# Test Credentials — Pritha Cabinet CRM

## Admin
- username: `admin`
- password: `Admin@2026`

## Employees
- username: `emp1`
- password: `Emp@2026`

Notes:
- Employee accounts are ADMIN-MANAGED (Team screen → Add / Remove). The owner deleted emp2–emp7; only `emp1` exists right now.
- The backend seeds admin + emp1..emp7 ONLY on a completely fresh database (first boot). Deleted employees are NOT re-created on restart.
- If a test needs more employee accounts, create them via POST /api/admin/users (admin token) and DELETE them afterwards.
- DB_NAME=pritha_cabinet, MONGO_URL=mongodb://localhost:27017
