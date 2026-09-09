#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "Feature: Each employee (and admin) can view their OWN sales and call report, aggregated by week and by month. New endpoint GET /api/stats/my-report + new screen my-report.tsx. Also restored missing backend/.env and frontend/.env files (were gitignored / not restored from GitHub)."

backend:
  - task: "my-report now includes invoices (count/revenue) + profit (sales+invoices), profit admin-only"
    implemented: true
    working: "NA"
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Extended GET /api/stats/my-report: each weekly/monthly bucket now also aggregates invoices — new field invoices_count (kept SEPARATE from sales_count per user), invoice total added into revenue, and new combined profit field = sale profit (amount - purchase_amount) + invoice profit (total - cost_total). Profit is ADMIN-ONLY: response includes is_admin flag; for non-admin users the 'profit' key is popped from every bucket (defence-in-depth) so employees never receive it. Verified locally via curl: admin sees profit + is_admin:true; emp1 has no profit key + is_admin:false. Seeded sale(1000, profit 1000) + invoice(total 1000, profit 400) → bucket sales_count=1, invoices_count=1, revenue=2000, profit=1400. Test data cleaned up."

  - task: "GET /api/stats/my-report — own weekly & monthly sales + call report"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "New endpoint returns logged-in user's OWN data only (filtered by user==username). Buckets: weekly (last 8 weeks, Monday-based) and monthly (last 6 calendar months). Each bucket has total calls, per-status breakdown (VALID_STATUS), sales_count, revenue. Verified locally via curl with seeded emp1 records: weekly and monthly buckets aggregate correctly (this-week 3 calls/1 sale, prior-week, last-month). Test data cleaned up after. Params weeks (max 52) and months (max 24) clamped."
        - working: true
          agent: "testing"
          comment: "Smoke test after deployment fix (removed quotes from backend/.env + restart). Tested with external URL https://open-my-project-10.preview.emergentagent.com. GET /api/stats/my-report?weeks=8&months=6 works for both emp1 and admin tokens - returns correct JSON structure with 8 weekly buckets and 6 monthly buckets, each containing calls, breakdown (per-status), sales_count, revenue. Confirmed data is scoped to the logged-in user (emp1 sees only emp1 data, admin sees only admin data). No regression detected."

backend_regression:
  - task: "Deployment smoke test after .env fix (removed quotes) + backend restart"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Comprehensive smoke test after deployment fix (removed surrounding quotes from backend/.env values and restarted backend). All tests PASSED: (1) GET /health responds 200 (public URL returns Expo HTML as expected, K8s probes on port 8001 work correctly). (2) POST /api/auth/login works for both admin (admin/Admin@2026) and emp1 (emp1/Emp@2026) - returns access_token + user object, confirms seeded users exist and auth works after restart. (3) GET /api/stats/my-report?weeks=8&months=6 with emp1 token returns correct JSON with 8 weekly + 6 monthly buckets, scoped to emp1's own data. (4) Same endpoint works with admin token, scoped to admin's own data. (5) Spot-checks: GET /api/stats/today returns expected structure (date, goal, total_calls, breakdown, pending_customers, total_customers). GET /api/stats/leaderboard returns rows array with 7 employees. NO REGRESSIONS DETECTED. Backend reads MONGO_URL/DB_NAME from unquoted .env correctly, DB connection working, all core endpoints functional."

  - task: "Deployment health probe (GET /health at root, no /api prefix)"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "GET http://localhost:8001/health returns 200 {\"status\":\"ok\"} and GET / returns 200 {\"status\":\"ok\",\"service\":\"pritha-cabinet\"}. Note: public URL routes only /api/* to backend; /health on public URL returns Expo HTML (not the JSON). K8s pod-level probes hitting port 8001 will work as intended."

  - task: "Smoke test after frontend deployment config fix (yarn.lock regeneration + Expo restart)"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Quick regression smoke test after frontend deployment config changes (regenerated yarn.lock, removed package-lock.json, restarted Expo with --tunnel). NO backend code was changed. Tested with external URL https://open-my-project-10.preview.emergentagent.com. ALL TESTS PASSED (4/4): (1) GET /api/health returns 404 as expected (public URL only routes /api/* to backend; health endpoint is at root /health, not /api/health - this is architectural behavior, not a regression). (2) POST /api/auth/login with admin credentials (admin/Admin@2026) returns 200 with access_token and user object. (3) GET /api/auth/me with admin Bearer token returns 200 with admin user details (username: admin, role: admin). (4) POST /api/auth/login with employee credentials (emp1/Emp@2026) returns 200 with access_token and user object. Core auth functionality verified working correctly. NO REGRESSIONS DETECTED - backend remains healthy after frontend deployment changes."

  - task: "GET /api/customers/search by name OR mobile"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Auth-required (401 without token). Empty q returns {customers:[],count:0}. Partial case-insensitive name match works. Digit-partial phone/phone_norm match works. is_mine flag correct per-user. All 8 seeded users (admin + emp1..emp7) can see customers regardless of assignee. Limit clamps to 1..100 (note: int(limit or 20) treats 0 as falsy → default 20, negative clamps to 1)."

  - task: "linked_receipts reference_no field on sales/collections/invoices/daybook"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Created sale + receipt with reference_no='REF-XYZ-123' and confirmed it flows back on GET /api/sales?scope=all. Same verified for /api/collections (COLLREF-*), /api/invoices (INVREF-*). Daybook due_collection/daily_sales/invoices sections all carry reference_no (string) on each linked_receipt. pdf_token still populated (regression OK). source_type field also present on daybook linked_receipts."

  - task: "Regression: /api/customers/lookup"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Lookup by phone returns {exists:true, customer:{...,is_mine:false}} correctly. Missing phone returns {exists:false}. Not broken by new /customers/search route ordering."

  - task: "Regression: /api/customers/{cust_id}/ledger"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Ledger endpoint returns 200 with expected structure. Route still resolves after adding /customers/search sibling route."

frontend:
  - task: "Login: admin password reported invalid — differentiate wrong-credentials from network/config errors"
    implemented: true
    working: true
    file: "/app/frontend/app/login.tsx, /app/frontend/src/lib/auth.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "USER BUG: 'password of admin is showing invalid'. RCA: backend login is fine (curl admin/Admin@2026 and emp1/Emp@2026 both return 200 + token on localhost AND public URL; DB seeded). The login screen's catch block previously showed 'Invalid username or password.' for ANY thrown error — including network/URL failures — so a connectivity/config problem (e.g. an APK built while frontend/.env with EXPO_PUBLIC_BACKEND_URL was missing) looked identical to a wrong password. Also restored the missing backend/.env + frontend/.env (were gitignored) and installed missing python deps (openpyxl/reportlab) so backend runs. FIX: login.tsx now inspects ApiError.status → 401/403 shows 'Invalid username or password.'; other ApiError shows 'Server error (N)'; non-ApiError (fetch/network) shows 'Can't reach the server. Check your internet connection…'. Verified locally via own Playwright on preview web: admin/Admin@2026 → dashboard (no error); wrong password → 'Invalid username or password.' stays on /login. Also hardened auth bootstrap with a storage-read timeout + 4s safety net so the splash can never hang. NEEDS formal UI test."
        - working: true
          agent: "testing"
          comment: "COMPREHENSIVE LOGIN FLOW TEST PASSED (5/5 steps). Tested on web preview https://a5d12c17-2a65-4082-bad6-428d840a89fc.preview.emergentagent.com. PRIMARY BUG FIX VERIFIED: (1) ✅ Admin login (admin/Admin@2026) - successfully navigated to dashboard showing 'Hi, Admin', NO error message visible (this is the PRIMARY bug fix - correct admin password now works without showing 'invalid' error). (2) ✅ Sign out - clicked More tab, clicked Sign out button (testID=row-signout), returned to login screen. (3) ✅ Employee login (emp1/Emp@2026) - successfully reached dashboard showing 'Hi, Employee 1'. (4) ✅ Wrong password test (admin/WrongPass123) - stayed on login page, error message displayed EXACTLY 'Invalid username or password.' (testID=login-error). (5) ✅ Correct password after wrong attempt - successfully navigated to dashboard, NO error message visible. BUG FIX CONFIRMED: The login screen now correctly differentiates between wrong credentials (shows 'Invalid username or password.') and successful login (no error). The user's reported issue 'admin password showing invalid' is FIXED - correct credentials (admin/Admin@2026 and emp1/Emp@2026) both login successfully without any error message."
    implemented: true
    working: true
    file: "/app/frontend/app/_layout.tsx, /app/frontend/src/lib/auth.tsx, /app/frontend/src/lib/api.ts"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "USER BUG: Published APK opens fine the first time but on the 2nd launch it stays on the splash/logo and never opens (also should open with no/poor internet). ROOT CAUSE (two parts): (1) app/index.tsx is a bare full-screen logo with no navigation; the Gate in _layout.tsx only redirected UNauthenticated users to /login and never moved an AUTHENTICATED user off the index/splash route, so on relaunch (already logged in) the app dead-ended on the logo. (2) AuthProvider.bootstrap did `await api.me()` (no timeout) BEFORE rendering, so on poor/no internet it hung; and any network error logged the user out (couldn't open offline). FIXES: (a) Gate now redirects `user && (inAuthGroup || atSplash)` -> /(tabs) so a signed-in user on the splash/login goes straight to the dashboard. (b) bootstrap now optimistically restores a locally cached user (new USER_KEY in AsyncStorage) and sets loading=false BEFORE any network call, then verifies via api.me() wrapped in an 8s withTimeout; it only signs out on a genuine 401/403 (ApiError.status) and keeps the cached session on network/timeout errors (offline-friendly). (c) api.req now throws ApiError with .status. Verified locally via standalone Playwright on preview: login (emp1/Emp@2026) -> dashboard; hard reload of '/' (relaunch sim) -> dashboard (previously blank/logo); reload with all /api/* requests aborted (offline sim) -> dashboard still opens from cache. Needs formal UI test."
        - working: true
          agent: "testing"
          comment: "COMPREHENSIVE UI TEST PASSED (4/4 steps). Tested on web preview https://open-my-project-10.preview.emergentagent.com with persistent browser session (simulates app relaunch). STEP 1 (LOGIN): ✅ PASSED - logged in with emp1/Emp@2026, reached dashboard showing 'Hi, Employee 1', 'Today's target 0/50', bottom tabs (Calls/Follow-ups/Progress/More). STEP 2 (RELAUNCH - CORE FIX): ✅ PASSED - performed 3 consecutive reloads of app root '/' in same session, ALL landed on dashboard with full content (NOT blank, NOT stuck on logo/splash, NOT perpetual spinner). This is the PRIMARY bug fix verification. STEP 3 (SIGN OUT then RELAUNCH): ✅ PASSED - clicked More tab, clicked Sign out (data-testid=row-signout), returned to login screen; reloaded '/' and stayed on login screen (not dashboard). STEP 4 (OFFLINE OPEN): ✅ PASSED - logged in, blocked all /api/** requests via Playwright route interception (simulating offline/no backend), reloaded '/', app opened to dashboard from cached session within 10s (blocked 5 API requests including /api/auth/me). App did NOT hang on spinner/logo, gracefully handled network failures. Console shows expected 'Failed to fetch' errors during offline test (correct behavior). BUG FIX VERIFIED: App now successfully relaunches to dashboard when user is logged in, handles sign out correctly, and opens offline from cache without hanging. The 'APK opens once then won't open on 2nd launch' bug is FIXED."

  - task: "My report screen — weekly/monthly toggle, sales + call breakdown"
    implemented: true
    working: "NA"
    file: "/app/frontend/app/my-report.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "New screen with Weekly/Monthly segmented toggle, summary strip (calls/sales/revenue totals) and per-period cards showing calls, sales_count, revenue and status breakdown pills. Added row 'My sales & call report' in More tab (visible to all) and registered route in _layout.tsx. Not yet UI-tested."

metadata:
  created_by: "testing_agent"
  version: "27"
  test_sequence: 27
  run_ui: false

test_plan:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    - agent: "main"
      message: "USER BUG 'admin password showing invalid' — please UI-test the LOGIN screen on the web preview. Credentials that MUST work: admin/Admin@2026 (admin) and emp1/Emp@2026 (employee). Backend is confirmed healthy (curl login returns 200 for both). Verify: (1) Load /login, sign in with admin/Admin@2026 → should reach the dashboard (no error text). (2) Sign out (More tab → Sign out), then login with emp1/Emp@2026 → dashboard. (3) Enter a WRONG password for admin → the inline error (testID login-error) should read exactly 'Invalid username or password.' and stay on /login. (4) Confirm a correct login does NOT show any error. Note: login screen may take a few seconds to render on first load (heavy dev web bundle) — wait/retry as needed. The fix changed only error messaging (network vs 401) — correct credentials must succeed."
    - agent: "main"
      message: "BUG FIX (APK opens once, won't open on 2nd launch) — please UI-test the RELAUNCH flow. Credentials: emp1/Emp@2026 (or admin/Admin@2026). Steps to verify: (1) Load /login, sign in -> should reach the dashboard ('Hi, ...', Today's target, bottom tabs Calls/Follow-ups/Progress/More). (2) SIMULATE APP RELAUNCH: navigate/reload the app root URL '/' in the SAME browser session (token persists in storage) -> MUST land on the dashboard, NOT a blank page or the logo/splash. Repeat reload 2-3 times. (3) Sign out -> should return to /login; reload '/' -> should stay on /login (not dashboard). (4) OFFLINE OPEN (optional if supported): with a valid saved session, block all /api/* requests then reload '/' -> the app should STILL open to the dashboard from cached session within ~8s (it must not hang on a spinner/logo). The key regression to catch: a logged-in user reloading '/' must never get stuck on the splash logo or a perpetual spinner. This is web-preview verification of a native (APK) relaunch bug."
    - agent: "main"
      message: "Implemented 'My report' feature: GET /api/stats/my-report (own weekly/monthly sales+calls) and frontend screen my-report.tsx with weekly/monthly toggle, accessible via More tab to all users. Backend verified locally with seeded+cleaned test data. Also restored missing backend/.env (MONGO_URL/DB_NAME=pritha_cabinet/EMERGENT_LLM_KEY) and frontend/.env (EXPO_PUBLIC_BACKEND_URL) — they were gitignored and not restored from GitHub, which had left backend crashing on startup."
    - agent: "main"
      message: "DEPLOYMENT FIX: Production EAS Android build was failing with 'No lockfile found in the project directory' because frontend had only package-lock.json (npm) but package.json declares packageManager yarn@1.22.22 and EAS uses yarn. FIX: generated frontend/yarn.lock via yarn install and removed package-lock.json. Additional deployment-agent items addressed: removed surrounding quotes from backend/.env values; added EXPO_TUNNEL_SUBDOMAIN + EXPO_USE_FAST_RESOLVER to frontend/.env; updated supervisor expo command to include --tunnel and installed @expo/ngrok (Expo now logs 'Tunnel connected/ready', preview loads). deployment_agent now returns status: pass with no blockers. Requesting a backend smoke test to confirm the .env change + restart did not regress anything (health, admin/emp login, /api/stats/my-report)."
    - agent: "testing"
      message: "Backend smoke/regression test COMPLETE - ALL TESTS PASSED (8/8). Verified after deployment fix (removed quotes from backend/.env + restart): (1) Health endpoints working (GET /health, GET /). (2) Auth working for both admin and emp1 - login returns access_token + user object. (3) GET /api/stats/my-report working for both emp1 and admin - returns correct structure with 8 weekly + 6 monthly buckets, properly scoped to each user's own data. (4) Regression checks passed: GET /api/stats/today and GET /api/stats/leaderboard both working correctly. Backend reads unquoted MONGO_URL/DB_NAME from .env correctly, DB connection established, all core functionality intact. NO REGRESSIONS DETECTED. The deployment fix was successful."
    - agent: "testing"
      message: "BUG FIX VERIFICATION COMPLETE ✅ - App relaunch / cold-start bug is FIXED. Tested all 4 steps on web preview with persistent browser session: (1) LOGIN ✅ - emp1/Emp@2026 reaches dashboard. (2) RELAUNCH ✅ - 3 consecutive reloads of '/' ALL landed on dashboard (NOT blank/logo/spinner) - PRIMARY BUG FIX VERIFIED. (3) SIGN OUT ✅ - sign out works, reload '/' stays on login. (4) OFFLINE OPEN ✅ - with API blocked, app opens to dashboard from cache within 10s without hanging. The 'APK opens once then won't open on 2nd launch' issue is resolved. App now correctly redirects authenticated users from splash to dashboard on relaunch, handles offline gracefully via cached session, and only signs out on genuine 401/403 (not network errors). All tests passed, no regressions detected."
    - agent: "testing"
      message: "SMOKE TEST AFTER FRONTEND DEPLOYMENT CONFIG FIX - ALL TESTS PASSED (4/4). Quick regression test after yarn.lock regeneration + Expo restart with --tunnel (NO backend code changed). Tested with external URL https://open-my-project-10.preview.emergentagent.com. Results: (1) GET /api/health returns 404 as expected (architectural behavior: public URL only routes /api/* to backend, health endpoint is at root /health). (2) Admin login (admin/Admin@2026) works - returns 200 with access_token and user object. (3) GET /api/auth/me with admin token works - returns 200 with admin user details. (4) Employee login (emp1/Emp@2026) works - returns 200 with access_token and user object. Core auth functionality verified working correctly. NO REGRESSIONS DETECTED - backend remains healthy after frontend deployment changes."
    - agent: "testing"
      message: "LOGIN BUG FIX VERIFICATION COMPLETE ✅ - 'Admin password showing invalid' bug is FIXED. Comprehensive UI test passed (5/5 steps) on web preview https://a5d12c17-2a65-4082-bad6-428d840a89fc.preview.emergentagent.com. PRIMARY VERIFICATION: (1) ✅ Admin login with CORRECT credentials (admin/Admin@2026) successfully navigates to dashboard showing 'Hi, Admin' with NO error message - this confirms the reported bug is fixed. (2) ✅ Employee login (emp1/Emp@2026) works correctly, shows 'Hi, Employee 1'. (3) ✅ Wrong password (admin/WrongPass123) correctly shows error 'Invalid username or password.' and stays on login page. (4) ✅ Correct password after wrong attempt successfully logs in with no error. (5) ✅ Sign out flow works correctly. The fix successfully differentiates between wrong credentials (401/403 → shows error) and correct credentials (no error, successful login). All test scenarios passed, no issues detected."
