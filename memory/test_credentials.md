# Test Credentials
# Agent writes here when creating/modifying auth credentials (admin accounts, test users).
# Testing agent reads this before auth tests. Fork/continuation agents read on startup.

## Pritha Cabinet CRM

Backend seeds these on startup (see backend/server.py lifespan).

| Role     | Username | Password    |
|----------|----------|-------------|
| Admin    | admin    | Admin@2026  |
| Employee | emp1     | Emp@2026    |
| Employee | emp2     | Emp@2026    |
| Employee | emp3     | Emp@2026    |
| Employee | emp4     | Emp@2026    |
| Employee | emp5     | Emp@2026    |
| Employee | emp6     | Emp@2026    |
| Employee | emp7     | Emp@2026    |

Login endpoint: POST /api/auth/login  { "username", "password" }
