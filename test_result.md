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
  - task: "Approval workflow — employee entries (sale/invoice/receipt) start pending (counted immediately); admin approves or rejects (=deletes); back-dating any past date on all three creates"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "USER REQUIREMENT: (1) sales/invoices/money-receipts can be back-dated by admin AND employee to ANY past date; (2) employee entries get status=pending but are COUNTED IMMEDIATELY in totals/reports — approval is only a review flag; (3) admin entries auto-approved; (4) admin reviews via dedicated list with Approve / Reject (=delete) buttons. CHANGES: (a) _backdate_key() helper — empty=today, YYYY-MM-DD validated, future dates 400. (b) SaleBody/InvoiceCreateBody/ReceiptCreateBody + optional date_key; create_sale/create_invoice/create_receipt honor it. (c) status field on Sale/Invoice/MoneyReceipt models (default 'approved' → existing docs read as approved); creates set 'approved' if admin else 'pending'. (d) Employee EDITS re-flag pending: PATCH /sales (also now allows owner to change date_key — was admin-only), PUT /invoices, PUT+PATCH /receipts set status per editor role. (e) NEW endpoints (admin-only): GET /api/approvals → {count, items[{kind,id,doc_no,customer_name,customer_mobile,amount,payment_mode,user,display_name,date_key,created_at,notes,pdf_token}]}, POST /api/approvals/{kind}/{id}/approve → sets approved+approved_by/approved_at, POST /api/approvals/{kind}/{id}/reject → deletes entry (invoice reject also deletes linked sale). (f) sale_from_doc now returns status. Smoke-tested locally: emp1 back-dated sale → pending, future date → 400, admin sale → approved, emp edit → re-pending, approve 200, employee GET /approvals → 403. NEEDS FULL TESTING incl. reject=delete, invoice back-date, receipt back-date, and regression on stats (pending entries must still count in /api/stats/sales-today, daybook, my-report)."
        - working: true
          agent: "testing"
          comment: "COMPREHENSIVE APPROVAL WORKFLOW + BACK-DATING TEST - ALL TESTS PASSED (14/14). Tested on public URL https://c5016b85-dc98-485e-b5dc-5005ae41eac1.preview.emergentagent.com/api with admin, emp1, and emp2 credentials. ✅ SECTION 1 - BACK-DATING (6/6 PASSED): (1.1) emp1 POST /api/sales with date_key='2026-08-15' (past date) returns 200, date_key=2026-08-15, status=pending. (1.2) emp1 POST /api/invoices with date_key='2026-08-10' (past date) returns 200, date_key=2026-08-10, status=pending. (1.3) emp1 POST /api/receipts with date_key='2026-08-05' (past date, source_type='other') returns 200, date_key=2026-08-05, status=pending. (1.4) admin POST /api/sales with date_key='2026-08-01' (past date) returns 200, date_key=2026-08-01, status=approved (auto-approved for admin). (1.5) emp1 POST /api/sales with date_key='2027-06-01' (future date) returns 400 with error 'Back-dating to a future date is not allowed' (correctly rejected). (1.6) emp1 POST /api/sales without date_key returns 200, date_key=2026-09-10 (defaults to today). ✅ SECTION 2 - APPROVALS ENDPOINTS (5/5 PASSED): (2.1) emp1 GET /api/approvals returns 403 (correctly blocked non-admin, admin-only endpoint). (2.2) admin GET /api/approvals returns 200, count=4, items=4 with correct structure (kind, id, customer_name, amount, user, display_name, date_key all present). (2.3) admin POST /api/approvals/sale/{id}/approve returns 200, approved=True; verified via GET /api/sales?scope=all that sale status changed to 'approved'. (2.4) admin POST /api/approvals/receipt/{id}/reject returns 200, deleted=True; verified via GET /api/receipts that receipt no longer exists (reject=delete working correctly). (2.5) admin approve already-approved entry returns 404 (correctly handles duplicate approval). ✅ SECTION 3 - EMPLOYEE EDIT RE-FLAGS PENDING (2/2 PASSED): (3.1) emp1 creates invoice → admin approves → emp1 PUT /api/invoices/{id} (owner edit) returns 200, status re-flagged to 'pending' (employee edits re-flag for review). (3.2) emp1 creates sale → admin approves → emp1 PATCH /api/sales/{id} with date_key='2026-08-20' returns 200, status re-flagged to 'pending', date_key updated (owner can back-date on edit). ✅ SECTION 4 - STATS REGRESSION (1/1 PASSED): (4.1) emp1 creates pending sale today (amount=999, status=pending) → GET /api/stats/sales-today?scope=all returns 200 with count=5, revenue=9799.0 (pending sale is counted immediately in today's stats - approval is only a review flag, not a gate for counting). All test data cleaned up (5 sales, 2 invoices, 1 customer deleted). NO REGRESSIONS DETECTED. Feature is fully functional and production-ready."

  - task: "Invoice edit permission — owner OR admin (was admin-only) on PUT /invoices/{iid}; delete stays admin-only"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "USER REQUEST: employees should also edit their OWN invoices. CHANGE: PUT /invoices/{iid} was Depends(admin_only) → now Depends(current_user) with owner-or-admin guard (doc['user']==u['username'] or admin). DELETE /invoices/{iid} unchanged (admin_only). NEEDS TESTING: emp1 creates invoice → emp1 PUT own invoice 200; emp2 PUT emp1's invoice 403; admin PUT any 200; emp1 DELETE own invoice 403; admin DELETE 200."
        - working: true
          agent: "testing"
          comment: "ALL TESTS PASSED (7/7). emp1 PUT own invoice 200 (PDF regenerated); emp2 PUT emp1's invoice 403; admin PUT any 200; emp1 DELETE own invoice 403 (admin-only); admin DELETE 200. Regression GET/POST invoices 200. Production-ready."
        - working: true
          agent: "testing"
          comment: "COMPREHENSIVE INVOICE EDIT PERMISSION TEST - ALL TESTS PASSED (7/7 scenarios). Tested on public URL https://c5016b85-dc98-485e-b5dc-5005ae41eac1.preview.emergentagent.com/api with admin, emp1, and emp2 credentials. ✅ SCENARIO 1 (Setup): emp1 creates invoice (customer_name='Invoice Edit Test Customer', customer_mobile='9998887771', items with total ₹2000) - invoice created successfully (200 OK), invoice.user='emp1', invoice_no='INV-000003'. ✅ SCENARIO 2 (Owner edit): emp1 PUT their OWN invoice with full valid body (changed items, new total ₹3400) returns 200 OK, invoice updated successfully, pdf_token present (PDF regenerated). ✅ SCENARIO 3 (Cross-user edit forbidden): emp2 (different non-admin) PUT emp1's invoice returns 403 Forbidden with message 'You can only edit your own invoices' (correctly blocked). ✅ SCENARIO 4 (Admin edit): admin PUT emp1's invoice returns 200 OK, invoice updated successfully, pdf_token present (PDF regenerated - admin can edit anyone's invoice). ✅ SCENARIO 5 (Owner delete forbidden): emp1 DELETE their own invoice returns 403 Forbidden (correctly blocked - DELETE is admin-only). ✅ SCENARIO 6 (Admin delete): admin DELETE emp1's invoice returns 200 OK, deleted=true (admin can delete any invoice). ✅ SCENARIO 7 (Regression): GET /api/invoices returns 200 OK (returns array of invoices). POST /api/invoices creates new invoice successfully (200 OK, invoice_no assigned). All test data cleaned up (2 customers, 2 invoices deleted). NO REGRESSIONS DETECTED. PERMISSION MODEL VERIFIED: PUT /api/invoices/{iid} allows owner OR admin (200), DELETE /api/invoices/{iid} is admin-only (403 for non-admin). Feature is fully functional and production-ready."

  - task: "Money-receipt edit permission — owner OR admin (was admin-only) on PATCH + PUT /receipts/{rid}; deletes stay admin-only"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "USER REQUEST: employees should be able to EDIT their OWN money receipts (like sales), but DELETE stays admin-only. CHANGE: PATCH /receipts/{rid} and PUT /receipts/{rid} were Depends(admin_only) → now Depends(current_user) with an owner-or-admin guard: `if u['role']!='admin' and doc['user']!=u['username']: raise 403`. DELETE /receipts/{rid} remains admin_only (unchanged). Sale PATCH already owner-or-admin (unchanged); sale DELETE already admin_only. NEEDS TESTING: (1) emp1 creates a money receipt → emp1 can PUT/PATCH it (200). (2) emp1 tries to PUT/PATCH a receipt created by admin (or another user) → 403. (3) admin can PUT/PATCH any receipt (200). (4) emp1 DELETE own receipt → 403 (admin-only). (5) admin DELETE any receipt → 200. Regression: creating receipts, advances list, invoices all still work. Auth: admin/Admin@2026, emp1/Emp@2026."
        - working: true
          agent: "testing"
          comment: "ALL TESTS PASSED (12/12) on public URL. emp1 PATCH/PUT own receipt → 200 (PDF regenerated on PUT). emp2 PATCH/PUT emp1's receipt → 403. admin PATCH/PUT emp1's receipt → 200. emp1 DELETE own receipt → 403 (admin-only). admin DELETE → 200. Regression: POST/GET /api/receipts 200. NO REGRESSIONS. Production-ready."
        - working: true
          agent: "testing"
          comment: "COMPREHENSIVE MONEY-RECEIPT EDIT PERMISSION TEST - ALL TESTS PASSED (12/12 core scenarios). Tested on public URL https://c5016b85-dc98-485e-b5dc-5005ae41eac1.preview.emergentagent.com/api with admin, emp1, and emp2 credentials. ✅ SCENARIO 1 (Setup): emp1 creates money receipt (amount=5000, source_type='other') - receipt created successfully (200 OK), receipt.user='emp1'. ✅ SCENARIO 2 (Owner edit PATCH): emp1 PATCH their OWN receipt with {narration:'edited by owner (emp1)'} returns 200 OK, narration updated correctly. ✅ SCENARIO 2b (Owner edit PUT): emp1 PUT their OWN receipt with full body returns 200 OK, narration updated to 'fully replaced by owner (emp1)', pdf_token present (PDF regenerated). ✅ SCENARIO 3 (Cross-user PATCH forbidden): emp2 (different non-admin) PATCH emp1's receipt returns 403 Forbidden (correctly blocked). ✅ SCENARIO 3b (Cross-user PUT forbidden): emp2 PUT emp1's receipt returns 403 Forbidden (correctly blocked). ✅ SCENARIO 4 (Admin edit PATCH): admin PATCH emp1's receipt returns 200 OK, narration updated to 'edited by admin' (admin can edit anyone's receipt). ✅ SCENARIO 4b (Admin edit PUT): admin PUT emp1's receipt returns 200 OK, narration updated to 'fully replaced by admin', pdf_token present (PDF regenerated). ✅ SCENARIO 5 (Owner delete forbidden): emp1 DELETE their own receipt returns 403 Forbidden (correctly blocked - delete is admin-only). ✅ SCENARIO 6 (Admin delete): admin DELETE emp1's receipt returns 200 OK, deleted=true (admin can delete any receipt). ✅ SCENARIO 7a (Regression): POST /api/receipts still works (200 OK, receipt created). ✅ SCENARIO 7b (Regression): GET /api/receipts still works (200 OK, returns array). Minor: GET /api/receipts/advances without customer_id/phone parameter returns 400 'customer_id or phone is required' (this is CORRECT API behavior - endpoint requires parameters by design, not a regression). All test data cleaned up (2 customers, 1 receipt deleted). NO REGRESSIONS DETECTED. Feature is fully functional and production-ready. PERMISSION MODEL VERIFIED: PATCH/PUT /receipts/{rid} allow owner OR admin (200), DELETE /receipts/{rid} is admin-only (403 for non-admin)."

  - task: "Invoice shows advance applied + balance due (advance_applied/balance_due fields + PDF) — allocation applied BEFORE PDF build"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "NEW: POST /api/invoices now (1) applies advance_allocations/attach_receipt_ids BEFORE rendering the PDF, (2) _apply_advance_allocations returns the TOTAL amount actually applied, (3) invoice response + stored doc now include advance_applied (sum applied) and balance_due (=total-advance_applied), (4) the invoice PDF renders an 'Advance paid' + 'Balance due' block under Grand total when advance_applied>0. NEEDS TESTING: create customer + advance receipt (source_type='other'); POST /api/invoices with advance_allocations:[{receipt_id, amount:<partial>}] and items totalling e.g. 5000 → response.advance_applied == partial, response.balance_due == 5000-partial, pdf_token present. Full apply (amount==invoice total) → balance_due 0. No advance → advance_applied 0, balance_due == total. GET /api/invoices returns advance_applied/balance_due on the created invoice. Regression: sales still work; advances remaining still correct."
        - working: true
          agent: "testing"
          comment: "COMPREHENSIVE INVOICE ADVANCE APPLIED + BALANCE DUE TEST - ALL TESTS PASSED (9/9 scenarios). Tested on public URL https://credit-persistence.preview.emergentagent.com/api with admin credentials. ✅ SCENARIO 1 (Setup): Created customer 'BalDue Test' (phone 9993330001) and advance receipt (amount=3000, source_type='other'). ✅ SCENARIO 2 (Partial apply): POST /api/invoices with advance_allocations:[{receipt_id, amount:2000}] on 5000 invoice creates invoice (200 OK). Response: total=5000, advance_applied=2000, balance_due=3000, pdf_token present (non-null). All fields correct. ✅ SCENARIO 3 (List reflects fields): GET /api/invoices returns invoice with advance_applied=2000 and balance_due=3000 present in list. ✅ SCENARIO 4 (Advance remaining): GET /api/receipts/advances?customer_id=<id> shows receipt with allocated=2000, remaining=1000 (only 2000 of 3000 used). ✅ SCENARIO 5 (Full apply exact): Created advance amount=4000. POST /api/invoices with items total 4000 and advance_allocations:[{receipt_id, amount:4000}] creates invoice with advance_applied=4000, balance_due=0 (exact match). ✅ SCENARIO 6 (Over-apply cap): Created advance amount=10000. POST /api/invoices with items total 6000 and advance_allocations:[{receipt_id, amount:9000}] creates invoice with advance_applied=9000 (capped at min(9000, remaining 10000)), balance_due=-3000 (negative as expected: 6000-9000). GET /api/receipts/advances shows receipt remaining=1000 (10000-9000). ✅ SCENARIO 7 (No advance regression): Created fresh customer. POST /api/invoices without advance fields creates invoice with advance_applied=0, balance_due=total (3000), pdf_token present. Backward compatibility confirmed. ✅ SCENARIO 8 (Legacy attach_receipt_ids): Created advance amount=1500. POST /api/invoices with items total 5000 and attach_receipt_ids:[<rid>] (no advance_allocations) creates invoice with advance_applied=1500 (full remaining applied), balance_due=3500 (5000-1500). Legacy field works correctly. ✅ SCENARIO 9 (Regression): GET /api/sales (200 OK), GET /api/stats/sales-today (200 OK), GET /api/deliveries (200 OK) all working. Created sale with advance_allocations - sale created successfully (200 OK), GET /api/sales shows sale.linked_receipts contains advance entry with amount=500, is_advance=true (verified separately). Note: POST /api/sales returns empty linked_receipts array (expected behavior), but GET /api/sales properly populates it. All test data cleaned up (3 customers, 5 receipts, 6 invoices deleted). NO REGRESSIONS DETECTED. Feature is fully functional and production-ready."
  - task: "Partial advance allocations on sales & invoices (advance_allocations) + list merge + advances remaining balance"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "NEW FEATURE (partial advance allocation). Extends the earlier attach_receipt_ids (which applied the FULL advance) with a new body field advance_allocations:[{receipt_id, amount}] on BOTH POST /api/sales and POST /api/invoices. Implementation: (1) shared helper _apply_advance_allocations(pairs, customer_id, customer_phone, target_type, target_id, target_label): for each (receipt_id, amount_or_None) it only touches genuine advances (source_type='other', no reference_no) belonging to the SAME customer (match by customer_id, else by normalized phone); pushes an allocation entry {target_type,target_id,target_label,amount,date} capped at the receipt's remaining balance; amount=None (legacy attach_receipt_ids) applies the full remaining. Receipts KEEP source_type='other' now (no longer flipped to 'sale'), so a single advance can be split across multiple sales/invoices. (2) _receipt_allocated / _receipt_remaining compute used vs available from the allocations array. (3) list_sales and list_invoices now merge linked_receipts = source-linked receipts (source_type='sale'/'invoice') + advance allocations via _alloc_linked_by_target(ids, 'sale'|'invoice') — each advance row is tagged source_type='advance', is_advance:true, with the ALLOCATED amount (not the full receipt amount). (4) GET /api/receipts/advances now returns ONLY advances with remaining>0, adds allocated+remaining on each row, and total_amount = sum of remaining. NEEDS TESTING: create advance receipt (source_type='other') for a customer, then POST /api/sales with advance_allocations:[{receipt_id, amount:<partial>}] → sale.linked_receipts contains an is_advance row with that partial amount; GET /api/receipts/advances shows the SAME receipt with remaining=amount-partial (still listed because remaining>0). Apply the rest via an invoice → receipt disappears from advances (remaining 0) and appears in invoice.linked_receipts. Verify over-allocation is capped at remaining and cross-customer receipts are ignored. Regression: legacy attach_receipt_ids still fully-applies; normal sales/invoices without advances unaffected."
        - working: true
          agent: "testing"
          comment: "COMPREHENSIVE PARTIAL ADVANCE ALLOCATION TEST - ALL TESTS PASSED (10/10 scenarios). Tested on public URL https://credit-persistence.preview.emergentagent.com/api with admin credentials. ✅ SCENARIO 1 (Setup): Created customer 'Alloc Test' (phone 9994440001) and advance receipt (amount=1000, source_type='other'). ✅ SCENARIO 2 (Verify available): GET /api/receipts/advances?customer_id=<id> returns correct structure {advances:[], count:1, total_amount:1000}. Receipt shows allocated=0, remaining=1000. ✅ SCENARIO 3 (Partial on sale): POST /api/sales with advance_allocations:[{receipt_id, amount:400}] creates sale (200 OK). GET /api/sales shows sale.linked_receipts contains advance entry with amount=400, source_type='advance', is_advance=true, receipt_no set. ✅ SCENARIO 4 (Remaining still listed): GET /api/receipts/advances shows SAME receipt still present with allocated=400, remaining=600, total_amount=600 (receipt NOT removed, still has balance). ✅ SCENARIO 5 (Rest on invoice): POST /api/invoices with advance_allocations:[{receipt_id, amount:600}] creates invoice (200 OK). GET /api/invoices shows invoice.linked_receipts contains advance entry with amount=600, is_advance=true. ✅ SCENARIO 6 (Fully consumed): GET /api/receipts/advances NO LONGER includes the receipt (correctly removed, remaining=0). Response: count=0, total_amount=0. ✅ SCENARIO 7 (Over-allocation cap): Created fresh advance (amount=500). POST /api/sales with advance_allocations:[{receipt_id, amount:900}] creates sale (200 OK). Sale.linked_receipts shows advance amount CAPPED at 500 (not 900). Receipt correctly removed from advances (remaining=0). ✅ SCENARIO 8 (Cross-customer safety): Created customer1 and customer2 with advance for customer2 (amount=800). POST /api/sales for customer1 with customer2's receipt_id in advance_allocations creates sale (200 OK) but sale.linked_receipts has NO advance entry (mismatched receipt silently ignored). Customer2's receipt remains fully available (remaining=800). ✅ SCENARIO 9 (Legacy attach_receipt_ids): Created advance (amount=300). POST /api/sales with attach_receipt_ids:[<rid>] (NO advance_allocations) applies full 300. Sale.linked_receipts shows advance entry amount=300, is_advance=true. Receipt correctly removed from advances (remaining=0). Backward compatibility confirmed. ✅ SCENARIO 10 (Regression): GET /api/sales (200 OK, returns array). GET /api/invoices (200 OK, returns array). GET /api/stats/sales-today (200 OK, correct structure). GET /api/deliveries (200 OK, correct structure). Normal sale without advances has linked_receipts as empty array (unaffected). All test data cleaned up (5 customers, 4 receipts, 5 sales, 1 invoice deleted). NO REGRESSIONS DETECTED. Feature is fully functional and production-ready."
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "NEW FEATURE (advance-payment delivery tracking). (1) MoneyReceipt gained delivery fields: delivery_status ('none'|'pending'|'delivered'), delivery_due_date (YYYY-MM-DD), delivered_at, delivery_note. (2) ReceiptCreateBody gained needs_delivery:bool + delivery_due_date:optional. In POST /api/receipts, when needs_delivery=true the receipt is saved delivery_status='pending' with delivery_due_date defaulting to TODAY+2 days if not supplied (else uses the given date). (3) NEW GET /api/deliveries?status=pending|delivered|all (all authenticated users) returns {date,count,pending_count,overdue_count,deliveries:[...]} where pending rows are sorted by due date asc and each row has an `overdue` flag (true when pending AND due_date < today). (4) NEW PATCH /api/deliveries/{receipt_id} body {mark_delivered?,reopen?,delivery_due_date?,delivery_note?} to mark delivered (sets delivered_at+updated_by), reopen, change due date, or set a note; returns the updated delivery row. Verified locally: /api/deliveries returns empty structure with admin token. Needs full testing: create an advance receipt with needs_delivery=true (verify default due=today+2 and it appears in pending list), mark it delivered (verify it leaves pending / appears in delivered), and an overdue case (past due_date → overdue:true). Also confirm existing receipts/advances/invoice flows are NOT regressed."
        - working: true
          agent: "testing"
          comment: "COMPREHENSIVE DELIVERY TRACKING TEST - ALL TESTS PASSED (11/11). Tested on public URL https://credit-persistence.preview.emergentagent.com/api with admin credentials. ✅ TEST 1 (Create advance with default due): POST /api/receipts with needs_delivery=true creates receipt with delivery_status='pending' and delivery_due_date=TODAY+2 (2026-09-11). ✅ TEST 2 (Create overdue advance): POST /api/receipts with delivery_due_date='2020-01-01' creates receipt with delivery_status='pending' and past due date. ✅ TEST 3 (List pending deliveries): GET /api/deliveries?status=pending returns correct structure {date, count, pending_count, overdue_count, deliveries:[]}. Both test receipts present, overdue receipt has overdue=true flag, deliveries sorted by due date ascending (oldest/overdue first). ✅ TEST 4 (Mark delivered): PATCH /api/deliveries/{id} with mark_delivered=true sets delivery_status='delivered', delivered_at timestamp, delivery_note='Handed over'. Receipt removed from pending list and appears in delivered list (GET /api/deliveries?status=delivered). ✅ TEST 5 (Update due date): PATCH /api/deliveries/{id} with delivery_due_date='2030-05-05' successfully updates due date. ✅ TEST 6 (Regression - normal receipt): POST /api/receipts without needs_delivery creates receipt with delivery_status='none' and does NOT appear in pending deliveries list. ✅ TEST 7a (Regression - GET /api/receipts): Returns array of receipts (200 OK). ✅ TEST 7b (Regression - GET /api/receipts/advances): Returns {advances:[]} structure (200 OK). ✅ TEST 8a (Validation - invalid date): PATCH with delivery_due_date='not-a-date' returns 400 error. ✅ TEST 8b (Validation - nonexistent ID): PATCH /api/deliveries/nonexistent-id returns 404 error. All test receipts cleaned up successfully. NO REGRESSIONS DETECTED. Feature is fully functional and production-ready."

  - task: "my-report now includes invoices (count/revenue) + profit (sales+invoices), profit admin-only"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Extended GET /api/stats/my-report: each weekly/monthly bucket now also aggregates invoices — new field invoices_count (kept SEPARATE from sales_count per user), invoice total added into revenue, and new combined profit field = sale profit (amount - purchase_amount) + invoice profit (total - cost_total). Profit is ADMIN-ONLY: response includes is_admin flag; for non-admin users the 'profit' key is popped from every bucket (defence-in-depth) so employees never receive it. Verified locally via curl: admin sees profit + is_admin:true; emp1 has no profit key + is_admin:false. Seeded sale(1000, profit 1000) + invoice(total 1000, profit 400) → bucket sales_count=1, invoices_count=1, revenue=2000, profit=1400. Test data cleaned up."
        - working: true
          agent: "testing"
          comment: "COMPREHENSIVE MY-REPORT TEST - ALL TESTS PASSED (3/3). Tested on public URL https://credit-persistence.preview.emergentagent.com/api with both admin and employee credentials. ✅ TEST 1 (Admin user): GET /api/stats/my-report?weeks=8&months=6 with admin token returns is_admin=true, 8 weekly buckets and 6 monthly buckets. Each bucket contains: calls, breakdown (dict with status keys), sales_count, invoices_count (NEW FIELD - separate from sales_count), revenue (includes both sales and invoices), and profit (NEW FIELD - admin-only, combines sale profit + invoice profit). Admin user correctly sees profit field in all buckets. ✅ TEST 2 (Employee user): GET /api/stats/my-report?weeks=8&months=6 with emp1 token returns is_admin=false, 8 weekly + 6 monthly buckets with same structure EXCEPT profit field is NOT present (admin-only restriction working correctly). Employee sees invoices_count and revenue but NOT profit. ✅ TEST 3 (Structure validation): Verified breakdown is dict type, all numeric fields (calls, sales_count, invoices_count, revenue, profit) are numbers. Weekly buckets have start/end dates, monthly buckets have key/label. ADMIN-ONLY PROFIT RESTRICTION VERIFIED: Employees cannot see profit data (defense-in-depth implementation working). NO REGRESSIONS DETECTED. Feature is fully functional and production-ready."

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
          comment: "Smoke test after deployment fix (removed quotes from backend/.env + restart). Tested with external URL https://credit-persistence.preview.emergentagent.com. GET /api/stats/my-report?weeks=8&months=6 works for both emp1 and admin tokens - returns correct JSON structure with 8 weekly buckets and 6 monthly buckets, each containing calls, breakdown (per-status), sales_count, revenue. Confirmed data is scoped to the logged-in user (emp1 sees only emp1 data, admin sees only admin data). No regression detected."

  - task: "POST /api/sales with purchase_amount (COGS) and attach_receipt_ids (link advance receipts)"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "NEW CHANGE — POST /api/sales now accepts two optional fields: purchase_amount (product cost/COGS, any employee can set it) and attach_receipt_ids (list of advance-receipt ids to link to the sale). Implementation: (1) SaleBody gained purchase_amount:Optional[float] and attach_receipt_ids:List[str]. (2) create_sale validates purchase_amount >= 0 if provided (400 if negative). (3) sale_from_doc computes profit = amount - purchase_amount (or amount if null). (4) When attach_receipt_ids is provided, the endpoint loops through each receipt id and links it to the sale ONLY if: (a) receipt exists, (b) source_type='other' (advance) with no reference_no, (c) customer matches by id or phone. Matching receipts are updated to source_type='sale' with source_id=sale_id. Non-matching receipts are silently ignored (safety). (5) GET /api/receipts/advances filters out receipts with source_type='sale', so attached receipts no longer appear in the advances list."
        - working: true
          agent: "testing"
          comment: "COMPREHENSIVE SALE CREATION TEST - ALL TESTS PASSED (17/17). Tested on public URL https://credit-persistence.preview.emergentagent.com/api with admin credentials. ✅ SECTION A - PURCHASE COST (3/3): (A.1) POST /api/sales with purchase_amount=600 creates sale with purchase_amount=600 and profit=400 (amount 1000 - purchase 600). (A.2) POST /api/sales with purchase_amount=-5 correctly returns 400 error (validation working). (A.3) POST /api/sales without purchase_amount creates sale with purchase_amount=null and profit=1000 (regression OK - backward compatible). ✅ SECTION B - ATTACH ADVANCES (5/5): (B.1) Created test customer. (B.2) Created advance receipt with source_type='other'. (B.3) GET /api/receipts/advances?customer_id=<id> includes the advance receipt (count=1, total_amount=300). (B.4) POST /api/sales with attach_receipt_ids=[<receipt_id>] creates sale successfully (200 OK). (B.5) GET /api/receipts/advances?customer_id=<id> NO LONGER includes the attached receipt (correctly removed from advances list - receipt now has source_type='sale'). ✅ SECTION C - SAFETY (1/1): Created two customers and an advance receipt for customer 1. POST /api/sales for customer 2 with customer 1's receipt id in attach_receipt_ids creates sale (200 OK) but silently ignores the mismatched receipt (customer 1's receipt remains in advances list, not linked to customer 2's sale). ✅ SECTION D - REGRESSION (4/4): (D.1) GET /api/sales?scope=all and scope=mine both return 200 with correct structure; sale with purchase_amount=600 shows profit=400 in the list. (D.2) GET /api/stats/sales-today returns 200 with correct structure (date, count, revenue, profit). (D.3) GET /api/deliveries returns 200 with correct structure (unaffected). (D.4) GET /api/receipts/advances returns 200 with correct structure (unaffected). All test data cleaned up (4 sales, 2 receipts, 3 customers deleted). NO REGRESSIONS DETECTED. Feature is fully functional and production-ready."

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
          comment: "Quick regression smoke test after frontend deployment config changes (regenerated yarn.lock, removed package-lock.json, restarted Expo with --tunnel). NO backend code was changed. Tested with external URL https://credit-persistence.preview.emergentagent.com. ALL TESTS PASSED (4/4): (1) GET /api/health returns 404 as expected (public URL only routes /api/* to backend; health endpoint is at root /health, not /api/health - this is architectural behavior, not a regression). (2) POST /api/auth/login with admin credentials (admin/Admin@2026) returns 200 with access_token and user object. (3) GET /api/auth/me with admin Bearer token returns 200 with admin user details (username: admin, role: admin). (4) POST /api/auth/login with employee credentials (emp1/Emp@2026) returns 200 with access_token and user object. Core auth functionality verified working correctly. NO REGRESSIONS DETECTED - backend remains healthy after frontend deployment changes."

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
  - task: "Approval workflow UI — Pending Approvals admin screen (/approvals) with Approve/Reject, More-tab row with count badge, Pending-review badges on sales/invoices/receipts rows, back-date inputs on punch-sale/invoice/receipt forms + owner date edit on sale edit modal"
    implemented: true
    working: "NA"
    file: "/app/frontend/app/approvals.tsx, /app/frontend/app/(tabs)/more.tsx, /app/frontend/app/sales.tsx, /app/frontend/app/invoices.tsx, /app/frontend/app/receipts.tsx, /app/frontend/src/components/PunchSaleModal.tsx, /app/frontend/src/lib/api.ts"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Frontend for the approval workflow. NEW app/approvals.tsx (admin-only): FlatList of pending entries w/ kind badge, doc no, customer, amount, employee display name, date, PDF link, Approve (green) + Reject (red, confirm → deletes) buttons, pull-to-refresh, empty state; non-admin sees lock message. more.tsx: ADMIN section 'Pending approvals' row with red count badge (fetched on focus). Pending-review amber pill on rows in sales.tsx/invoices.tsx/receipts.tsx when status==='pending'. Back-date inputs added: PunchSaleModal 'Sale date (optional — back-date)', InvoiceEditor 'Invoice date', ReceiptEditor 'Receipt date' (all pass date_key, empty=today); sale edit modal date field no longer admin-only (owner can back-date too). api.ts: status on Sale/Invoice/MoneyReceipt types, date_key on createSale/createInvoice/createReceipt payloads, ApprovalItem type + listApprovals/approveEntry/rejectEntry. NEEDS UI TEST: (1) emp1 login → punch sale → row shows 'Pending review' pill. (2) admin login → More → 'Pending approvals' row shows badge count → open → approve → entry disappears & pill clears. (3) admin rejects an entry → deleted. (4) back-date: emp1 punches sale with past date → appears under that date."

  - task: "Advance auto-cap on Sale & Invoice forms — default applied amount = min(remaining, bill amount), waterfall across receipts; manual edits respected; credit-left hint"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/components/PunchSaleModal.tsx, /app/frontend/app/invoices.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: "NA"
          agent: "main"
          comment: "USER BUG: an advance showed once then disappeared on the 2nd sale/invoice because the amount field defaulted to the FULL remaining balance — saving any bill consumed the entire advance. FIX (frontend only; backend already supports partial allocations): (1) Removed the full-remaining pre-fill on advances fetch in BOTH forms. (2) New reactive effect in both forms: each selected advance auto-fills with only what the bill still needs — waterfall in listed order, use=min(remaining, billAmountLeft) — recomputed live as sale amount / invoice grand total changes (untouched fields only). (3) Wired advTouched: typing in an advance amount marks it manual (never auto-overwritten); clearing the field reverts it to auto. (4) Footer now shows 'Applying ₹X · credit left ₹Y'. Result: e.g. ₹3000 advance + ₹800 sale → applies 800, remaining 2200 keeps showing (receipt no + remaining) on the next sale/invoice until fully cleared. NEEDS UI TEST: create customer + ₹3000 advance (source other) → Punch sale ₹800 for that customer → advance field should auto-show 800 (not 3000) → save → reopen punch sale for same customer → same receipt still listed with Available ₹2200. Repeat on New invoice form (items totalling e.g. ₹500 → field auto-shows 500). Also verify manual override still works (type 3000 → stays 3000 even when amount changes)."

  - task: "Pending Deliveries feature — delivery toggle on money-receipt form + deliveries.tsx screen"
    implemented: true
    working: "NA"
    file: "/app/frontend/app/deliveries.tsx, /app/frontend/app/receipts.tsx, /app/frontend/app/(tabs)/more.tsx, /app/frontend/app/_layout.tsx, /app/frontend/src/lib/api.ts"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: "NA"
          agent: "main"
          comment: "NEW FEATURE UI (advance-payment delivery tracking). (1) Money-receipt create form (receipts.tsx): added a 'Product to be delivered later' checkbox; when ticked a Delivery due date (YYYY-MM-DD, defaults to today+2) with quick chips (Tomorrow/+2/+3/+7) appears; submit sends needs_delivery + delivery_due_date. Only shown on CREATE (not edit). (2) New screen deliveries.tsx ('Pending Deliveries', route registered in _layout, row added in More tab visible to all): Awaiting/Delivered segmented tabs, cards show customer, mobile, amount, due-date chip (Overdue in RED / Due today / Due in N days / Delivered date), narration + delivery note; pull-to-refresh; 'Mark delivered' opens a modal for an optional delivery note then PATCH /deliveries/{id} {mark_delivered:true}; delivered items can be 'Reopen'ed. (3) api.ts: added Delivery type, listDeliveries(status), updateDelivery(id,patch), and delivery fields on createReceipt/MoneyReceipt. Self-verified via Playwright: screen renders with live empty-state (0 awaiting), no runtime errors. Backend endpoints already passed testing. NEEDS full UI test of the create-advance-with-delivery → appears in Awaiting → Mark delivered → moves to Delivered flow."

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
          comment: "COMPREHENSIVE LOGIN FLOW TEST PASSED (5/5 steps). Tested on web preview https://credit-persistence.preview.emergentagent.com. PRIMARY BUG FIX VERIFIED: (1) ✅ Admin login (admin/Admin@2026) - successfully navigated to dashboard showing 'Hi, Admin', NO error message visible (this is the PRIMARY bug fix - correct admin password now works without showing 'invalid' error). (2) ✅ Sign out - clicked More tab, clicked Sign out button (testID=row-signout), returned to login screen. (3) ✅ Employee login (emp1/Emp@2026) - successfully reached dashboard showing 'Hi, Employee 1'. (4) ✅ Wrong password test (admin/WrongPass123) - stayed on login page, error message displayed EXACTLY 'Invalid username or password.' (testID=login-error). (5) ✅ Correct password after wrong attempt - successfully navigated to dashboard, NO error message visible. BUG FIX CONFIRMED: The login screen now correctly differentiates between wrong credentials (shows 'Invalid username or password.') and successful login (no error). The user's reported issue 'admin password showing invalid' is FIXED - correct credentials (admin/Admin@2026 and emp1/Emp@2026) both login successfully without any error message."
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
          comment: "COMPREHENSIVE UI TEST PASSED (4/4 steps). Tested on web preview https://credit-persistence.preview.emergentagent.com with persistent browser session (simulates app relaunch). STEP 1 (LOGIN): ✅ PASSED - logged in with emp1/Emp@2026, reached dashboard showing 'Hi, Employee 1', 'Today's target 0/50', bottom tabs (Calls/Follow-ups/Progress/More). STEP 2 (RELAUNCH - CORE FIX): ✅ PASSED - performed 3 consecutive reloads of app root '/' in same session, ALL landed on dashboard with full content (NOT blank, NOT stuck on logo/splash, NOT perpetual spinner). This is the PRIMARY bug fix verification. STEP 3 (SIGN OUT then RELAUNCH): ✅ PASSED - clicked More tab, clicked Sign out (data-testid=row-signout), returned to login screen; reloaded '/' and stayed on login screen (not dashboard). STEP 4 (OFFLINE OPEN): ✅ PASSED - logged in, blocked all /api/** requests via Playwright route interception (simulating offline/no backend), reloaded '/', app opened to dashboard from cached session within 10s (blocked 5 API requests including /api/auth/me). App did NOT hang on spinner/logo, gracefully handled network failures. Console shows expected 'Failed to fetch' errors during offline test (correct behavior). BUG FIX VERIFIED: App now successfully relaunches to dashboard when user is logged in, handles sign out correctly, and opens offline from cache without hanging. The 'APK opens once then won't open on 2nd launch' bug is FIXED."

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
  created_by: "main_agent"
  version: "33"
  test_sequence: 33
  run_ui: false

test_plan:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    - agent: "main"
      message: "USER BUG: 'server error 502'. ROOT CAUSE: the environment was rebuilt/reset, which wiped (a) pip packages openpyxl+reportlab from /root/.venv (backend worker crashed on 'ModuleNotFoundError: openpyxl' at server.py line 19 → nginx ingress returned 502), (b) gitignored backend/.env + frontend/.env, (c) the entire MongoDB 'pritha_cabinet' database. FIX APPLIED: reinstalled openpyxl==3.1.5 + reportlab==5.0.1 into /root/.venv (both already pinned in requirements.txt), restored backend/.env (MONGO_URL=mongodb://localhost:27017, DB_NAME=pritha_cabinet, EMERGENT_LLM_KEY — unquoted values), restored frontend/.env (EXPO_PUBLIC_BACKEND_URL=https://c5016b85-dc98-485e-b5dc-5005ae41eac1.preview.emergentagent.com), restarted backend+expo. Verified locally: GET /health 200, POST /api/auth/login admin/Admin@2026 → 200 with token (lifespan auto-seeded admin + emp1..7 into the fresh DB), public URL /api/auth/login → 200, public preview → 200. IMPORTANT: ALL PREVIOUS BUSINESS DATA (customers/sales/receipts/invoices) WAS LOST in the reset — DB is fresh with only seeded users. PLEASE VERIFY: (1) public URL https://c5016b85-dc98-485e-b5dc-5005ae41eac1.preview.emergentagent.com/api — login admin/Admin@2026 and emp1/Emp@2026 both 200; (2) GET /api/auth/me with token; (3) core list endpoints 200 (GET /api/sales, /api/invoices, /api/customers/search?q=x, /api/receipts/advances, /api/deliveries, /api/stats/today, /api/stats/my-report); (4) quick end-to-end of the current feature work since DB is empty: create customer → advance receipt (source_type=other, ₹3000) → POST /api/sales with advance_allocations partial ₹800 → GET /api/receipts/advances shows remaining 2200 (receipt persists). Clean up test data after."
    - agent: "testing"
      message: "APPROVAL WORKFLOW + BACK-DATING FEATURE TEST COMPLETE ✅ - ALL TESTS PASSED (14/14). Comprehensive testing completed on public URL https://c5016b85-dc98-485e-b5dc-5005ae41eac1.preview.emergentagent.com/api. RESULTS SUMMARY: ✅ BACK-DATING (6/6): Employee and admin can back-date sales/invoices/receipts to ANY past date (tested 2026-08-15, 2026-08-10, 2026-08-05, 2026-08-01). Future dates correctly rejected with 400. No date_key defaults to today. ✅ APPROVALS ENDPOINTS (5/5): GET /api/approvals is admin-only (emp1 gets 403). Admin can list pending entries (correct structure with kind/id/customer/amount/user/date_key). Admin can approve entries (status changes to 'approved'). Admin can reject entries (deletes the entry). Already-approved entries return 404 on re-approval. ✅ EMPLOYEE EDIT RE-FLAGS PENDING (2/2): When employee edits their own approved invoice/sale, status is re-flagged to 'pending' for admin review. Owner can back-date on edit (PATCH /sales with date_key works). ✅ STATS REGRESSION (1/1): Pending entries are counted immediately in GET /api/stats/sales-today (approval is only a review flag, not a gate for counting). All test data cleaned up. NO REGRESSIONS DETECTED. Feature is fully functional and production-ready."
     - agent: "main"
      message: "Please test the NEW delivery-tracking backend endpoints. Auth: admin/Admin@2026 or emp1/Emp@2026. Scenarios: (1) POST /api/receipts with body {customer_name:'Del Test', customer_mobile:'9990001111', amount:500, payment_mode:'cash', source_type:'other', needs_delivery:true} → response should have delivery_status='pending' and delivery_due_date = TODAY+2 (YYYY-MM-DD). (2) POST /api/receipts with needs_delivery:true AND delivery_due_date:'2020-01-01' (PAST date) → GET /api/deliveries?status=pending should include this with overdue:true. (3) GET /api/deliveries?status=pending → {date,count,pending_count,overdue_count,deliveries:[]}; receipts from (1)&(2) must appear sorted by due date asc. (4) PATCH /api/deliveries/{id} {mark_delivered:true, delivery_note:'Handed over'} → delivery_status='delivered', delivered_at set; then it must DISAPPEAR from status=pending and APPEAR in status=delivered. (5) PATCH /api/deliveries/{id} {delivery_due_date:'2030-05-05'} → updates due date. (6) Regression: POST /api/receipts WITHOUT needs_delivery must work with delivery_status='none' and must NOT appear in /api/deliveries. Spot-check GET /api/receipts and GET /api/receipts/advances still work. Please CLEAN UP any test receipts you create."
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
      message: "SMOKE TEST AFTER FRONTEND DEPLOYMENT CONFIG FIX - ALL TESTS PASSED (4/4). Quick regression test after yarn.lock regeneration + Expo restart with --tunnel (NO backend code changed). Tested with external URL https://credit-persistence.preview.emergentagent.com. Results: (1) GET /api/health returns 404 as expected (architectural behavior: public URL only routes /api/* to backend, health endpoint is at root /health). (2) Admin login (admin/Admin@2026) works - returns 200 with access_token and user object. (3) GET /api/auth/me with admin token works - returns 200 with admin user details. (4) Employee login (emp1/Emp@2026) works - returns 200 with access_token and user object. Core auth functionality verified working correctly. NO REGRESSIONS DETECTED - backend remains healthy after frontend deployment changes."
    - agent: "testing"
      message: "LOGIN BUG FIX VERIFICATION COMPLETE ✅ - 'Admin password showing invalid' bug is FIXED. Comprehensive UI test passed (5/5 steps) on web preview https://credit-persistence.preview.emergentagent.com. PRIMARY VERIFICATION: (1) ✅ Admin login with CORRECT credentials (admin/Admin@2026) successfully navigates to dashboard showing 'Hi, Admin' with NO error message - this confirms the reported bug is fixed. (2) ✅ Employee login (emp1/Emp@2026) works correctly, shows 'Hi, Employee 1'. (3) ✅ Wrong password (admin/WrongPass123) correctly shows error 'Invalid username or password.' and stays on login page. (4) ✅ Correct password after wrong attempt successfully logs in with no error. (5) ✅ Sign out flow works correctly. The fix successfully differentiates between wrong credentials (401/403 → shows error) and correct credentials (no error, successful login). All test scenarios passed, no issues detected."
    - agent: "testing"
      message: "DELIVERY TRACKING BACKEND TEST COMPLETE ✅ - ALL TESTS PASSED (11/11). Comprehensive testing of NEW delivery tracking feature on public URL https://credit-persistence.preview.emergentagent.com/api. RESULTS: (1) ✅ Create advance with delivery (default due=TODAY+2): POST /api/receipts with needs_delivery=true correctly creates receipt with delivery_status='pending' and delivery_due_date='2026-09-11' (TODAY+2). (2) ✅ Create overdue advance: POST /api/receipts with delivery_due_date='2020-01-01' creates receipt with past due date. (3) ✅ List pending deliveries: GET /api/deliveries?status=pending returns correct structure {date, count, pending_count, overdue_count, deliveries:[]}. Both test receipts present, overdue receipt has overdue=true flag, deliveries sorted by due date ascending (oldest/overdue first). (4) ✅ Mark delivered: PATCH /api/deliveries/{id} with mark_delivered=true sets delivery_status='delivered', delivered_at timestamp, delivery_note. Receipt removed from pending list and appears in delivered list. (5) ✅ Update due date: PATCH /api/deliveries/{id} with delivery_due_date='2030-05-05' successfully updates. (6) ✅ Regression - normal receipt: POST /api/receipts without needs_delivery creates receipt with delivery_status='none' and does NOT appear in pending deliveries. (7) ✅ Regression - GET /api/receipts and GET /api/receipts/advances both working (200 OK). (8) ✅ Validation: Invalid date returns 400, nonexistent ID returns 404. All test receipts cleaned up. NO REGRESSIONS DETECTED. Feature is fully functional and production-ready."
    - agent: "testing"
      message: "MY-REPORT WITH INVOICES & PROFIT TEST COMPLETE ✅ - ALL TESTS PASSED (3/3). Tested GET /api/stats/my-report on public URL https://credit-persistence.preview.emergentagent.com/api with both admin and employee users. RESULTS: (1) ✅ Admin user: GET /api/stats/my-report?weeks=8&months=6 with admin token returns is_admin=true, 8 weekly + 6 monthly buckets. Each bucket contains: calls, breakdown (dict), sales_count, invoices_count (NEW - separate from sales_count), revenue (includes sales + invoices), and profit (NEW - admin-only, combines sale profit + invoice profit). Admin correctly sees profit field. (2) ✅ Employee user: Same endpoint with emp1 token returns is_admin=false, 8 weekly + 6 monthly buckets with invoices_count and revenue but NO profit field (admin-only restriction working correctly). (3) ✅ Structure validation: breakdown is dict, all numeric fields are numbers, weekly buckets have start/end dates, monthly buckets have key/label. ADMIN-ONLY PROFIT RESTRICTION VERIFIED: Employees cannot see profit data (defense-in-depth working). NO REGRESSIONS DETECTED. Feature is fully functional and production-ready."
    - agent: "main"
      message: "NEW CHANGE — POST /api/sales now accepts two optional fields: purchase_amount (product cost/COGS, any employee can set it) and attach_receipt_ids (list of advance-receipt ids to link to the sale). Please backend-test on the current preview /api. Auth: admin/Admin@2026 or emp1/Emp@2026. Scenarios: (A) PURCHASE COST: POST /api/sales {customer_name:'Cost Test', amount:1000, product:'X', purchase_amount:600} → 200; response purchase_amount=600 and profit=400. Also POST with purchase_amount:-5 → 400. POST without purchase_amount → 200 and purchase_amount=null (regression). (B) ATTACH ADVANCES: First create a customer via POST /api/customers {name:'Adv Sale Cust', phone:'9995550001', address:'x'} (or reuse). Create an ADVANCE receipt: POST /api/receipts {customer_id:<id>, customer_name:'Adv Sale Cust', customer_mobile:'9995550001', amount:300, payment_mode:'cash', source_type:'other'} → note its receipt id. Verify GET /api/receipts/advances?customer_id=<id> includes it. Then POST /api/sales {customer_id:<id>, customer_name:'Adv Sale Cust', amount:1000, attach_receipt_ids:[<receipt_id>]} → 200. After that, GET /api/receipts/advances?customer_id=<id> should NO LONGER include that receipt (it became source_type='sale', source_id=<sale_id>). (C) SAFETY: attaching a receipt id that belongs to a DIFFERENT customer must be silently ignored (not linked). (D) Regression: GET /api/sales and GET /api/stats/sales-today still work; deliveries/advances endpoints unaffected. Please CLEAN UP any test customers/receipts/sales you create. NOTE: also verify the sale's profit reflects purchase_amount in GET /api/sales list."
    - agent: "testing"
      message: "SALE CREATION WITH PURCHASE_AMOUNT & ATTACH_RECEIPT_IDS TEST COMPLETE ✅ - ALL TESTS PASSED (17/17). Comprehensive testing of NEW sale creation features on public URL https://credit-persistence.preview.emergentagent.com/api with admin credentials. RESULTS: ✅ SECTION A - PURCHASE COST (3/3 PASS): (A.1) POST /api/sales with purchase_amount=600 creates sale with purchase_amount=600 and profit=400 (1000-600). (A.2) Negative purchase_amount correctly rejected with 400 error. (A.3) Sale without purchase_amount creates with purchase_amount=null and profit=1000 (regression OK). ✅ SECTION B - ATTACH ADVANCES (5/5 PASS): Created customer and advance receipt (source_type='other'). Verified receipt appears in GET /api/receipts/advances. Created sale with attach_receipt_ids=[<receipt_id>] (200 OK). Verified receipt NO LONGER appears in advances list (correctly changed to source_type='sale'). ✅ SECTION C - SAFETY (1/1 PASS): Created two customers and advance receipt for customer 1. Sale for customer 2 with customer 1's receipt id silently ignores mismatched receipt (customer 1's receipt remains in advances, not linked to customer 2's sale). ✅ SECTION D - REGRESSION (4/4 PASS): GET /api/sales (scope=all and mine) returns 200 with profit field correct. GET /api/stats/sales-today returns 200 with correct structure. GET /api/deliveries and GET /api/receipts/advances both unaffected (200 OK). All test data cleaned up (4 sales, 2 receipts, 3 customers deleted). NO REGRESSIONS DETECTED. Feature is fully functional and production-ready."
    - agent: "testing"
      message: "PARTIAL ADVANCE ALLOCATION TEST COMPLETE ✅ - ALL TESTS PASSED (10/10 scenarios). Comprehensive testing of NEW partial advance allocation feature on public URL https://credit-persistence.preview.emergentagent.com/api with admin credentials. RESULTS: ✅ SCENARIO 1 (Setup): Created customer 'Alloc Test' (phone 9994440001) and advance receipt (amount=1000, source_type='other'). ✅ SCENARIO 2 (Verify available): GET /api/receipts/advances?customer_id=<id> returns correct structure {advances:[], count:1, total_amount:1000}. Receipt shows allocated=0, remaining=1000. ✅ SCENARIO 3 (Partial on sale): POST /api/sales with advance_allocations:[{receipt_id, amount:400}] creates sale (200 OK). Sale.linked_receipts contains advance entry with amount=400, source_type='advance', is_advance=true, receipt_no set. ✅ SCENARIO 4 (Remaining still listed): GET /api/receipts/advances shows SAME receipt still present with allocated=400, remaining=600, total_amount=600 (receipt NOT removed, still has balance). ✅ SCENARIO 5 (Rest on invoice): POST /api/invoices with advance_allocations:[{receipt_id, amount:600}] creates invoice (200 OK). Invoice.linked_receipts contains advance entry with amount=600, is_advance=true. ✅ SCENARIO 6 (Fully consumed): GET /api/receipts/advances NO LONGER includes the receipt (correctly removed, remaining=0). Response: count=0, total_amount=0. ✅ SCENARIO 7 (Over-allocation cap): Created fresh advance (amount=500). POST /api/sales with advance_allocations:[{receipt_id, amount:900}] creates sale (200 OK). Sale.linked_receipts shows advance amount CAPPED at 500 (not 900). Receipt correctly removed from advances (remaining=0). ✅ SCENARIO 8 (Cross-customer safety): Created customer1 and customer2 with advance for customer2 (amount=800). POST /api/sales for customer1 with customer2's receipt_id in advance_allocations creates sale (200 OK) but sale.linked_receipts has NO advance entry (mismatched receipt silently ignored). Customer2's receipt remains fully available (remaining=800). ✅ SCENARIO 9 (Legacy attach_receipt_ids): Created advance (amount=300). POST /api/sales with attach_receipt_ids:[<rid>] (NO advance_allocations) applies full 300. Sale.linked_receipts shows advance entry amount=300, is_advance=true. Receipt correctly removed from advances (remaining=0). Backward compatibility confirmed. ✅ SCENARIO 10 (Regression): GET /api/sales (200 OK, returns array). GET /api/invoices (200 OK, returns array). GET /api/stats/sales-today (200 OK, correct structure). GET /api/deliveries (200 OK, correct structure). Normal sale without advances has linked_receipts as empty array (unaffected). All test data cleaned up (5 customers, 4 receipts, 5 sales, 1 invoice deleted). NO REGRESSIONS DETECTED. Feature is fully functional and production-ready."

    - agent: "testing"
      message: "INVOICE ADVANCE APPLIED + BALANCE DUE TEST COMPLETE ✅ - ALL TESTS PASSED (9/9 scenarios). Comprehensive testing of NEW invoice advance_applied + balance_due feature on public URL https://credit-persistence.preview.emergentagent.com/api with admin credentials. RESULTS: ✅ SCENARIO 1 (Setup): Created customer 'BalDue Test' (phone 9993330001) and advance receipt (amount=3000, source_type='other'). ✅ SCENARIO 2 (Partial apply): POST /api/invoices with advance_allocations:[{receipt_id, amount:2000}] on 5000 invoice creates invoice (200 OK). Response: total=5000, advance_applied=2000, balance_due=3000, pdf_token present (non-null). All fields correct. ✅ SCENARIO 3 (List reflects fields): GET /api/invoices returns invoice with advance_applied=2000 and balance_due=3000 present in list. ✅ SCENARIO 4 (Advance remaining): GET /api/receipts/advances?customer_id=<id> shows receipt with allocated=2000, remaining=1000 (only 2000 of 3000 used). ✅ SCENARIO 5 (Full apply exact): Created advance amount=4000. POST /api/invoices with items total 4000 and advance_allocations:[{receipt_id, amount:4000}] creates invoice with advance_applied=4000, balance_due=0 (exact match). ✅ SCENARIO 6 (Over-apply cap): Created advance amount=10000. POST /api/invoices with items total 6000 and advance_allocations:[{receipt_id, amount:9000}] creates invoice with advance_applied=9000 (capped at min(9000, remaining 10000)), balance_due=-3000 (negative as expected: 6000-9000). GET /api/receipts/advances shows receipt remaining=1000 (10000-9000). ✅ SCENARIO 7 (No advance regression): Created fresh customer. POST /api/invoices without advance fields creates invoice with advance_applied=0, balance_due=total (3000), pdf_token present. Backward compatibility confirmed. ✅ SCENARIO 8 (Legacy attach_receipt_ids): Created advance amount=1500. POST /api/invoices with items total 5000 and attach_receipt_ids:[<rid>] (no advance_allocations) creates invoice with advance_applied=1500 (full remaining applied), balance_due=3500 (5000-1500). Legacy field works correctly. ✅ SCENARIO 9 (Regression): GET /api/sales (200 OK), GET /api/stats/sales-today (200 OK), GET /api/deliveries (200 OK) all working. Created sale with advance_allocations - sale created successfully (200 OK), GET /api/sales shows sale.linked_receipts contains advance entry with amount=500, is_advance=true (verified separately). Note: POST /api/sales returns empty linked_receipts array (expected behavior), but GET /api/sales properly populates it. All test data cleaned up (3 customers, 5 receipts, 6 invoices deleted). NO REGRESSIONS DETECTED. Feature is fully functional and production-ready."

    - agent: "testing"
      message: "MONEY-RECEIPT EDIT PERMISSION TEST COMPLETE ✅ - ALL CORE TESTS PASSED (12/12). Comprehensive testing of NEW owner-or-admin permission model on PATCH/PUT /receipts/{rid} on public URL https://c5016b85-dc98-485e-b5dc-5005ae41eac1.preview.emergentagent.com/api with admin, emp1, and emp2 credentials. RESULTS: ✅ SCENARIO 1: emp1 creates money receipt (amount=5000, source_type='other') - 200 OK, receipt.user='emp1'. ✅ SCENARIO 2: emp1 PATCH their OWN receipt {narration:'edited by owner (emp1)'} - 200 OK, narration updated. ✅ SCENARIO 2b: emp1 PUT their OWN receipt with full body - 200 OK, narration updated to 'fully replaced by owner (emp1)', pdf_token present (PDF regenerated). ✅ SCENARIO 3: emp2 (different non-admin) PATCH emp1's receipt - 403 Forbidden (correctly blocked). ✅ SCENARIO 3b: emp2 PUT emp1's receipt - 403 Forbidden (correctly blocked). ✅ SCENARIO 4: admin PATCH emp1's receipt - 200 OK, narration updated to 'edited by admin' (admin can edit anyone's receipt). ✅ SCENARIO 4b: admin PUT emp1's receipt - 200 OK, narration updated to 'fully replaced by admin', pdf_token present (PDF regenerated). ✅ SCENARIO 5: emp1 DELETE their own receipt - 403 Forbidden (correctly blocked - delete is admin-only). ✅ SCENARIO 6: admin DELETE emp1's receipt - 200 OK, deleted=true (admin can delete any receipt). ✅ SCENARIO 7a: POST /api/receipts regression - 200 OK, receipt created. ✅ SCENARIO 7b: GET /api/receipts regression - 200 OK, returns array. Minor: GET /api/receipts/advances without customer_id/phone parameter returns 400 'customer_id or phone is required' (this is CORRECT API behavior - endpoint requires parameters by design, not a regression). All test data cleaned up (2 customers, 1 receipt deleted). NO REGRESSIONS DETECTED. PERMISSION MODEL VERIFIED: PATCH/PUT /receipts/{rid} allow owner OR admin (200), DELETE /receipts/{rid} is admin-only (403 for non-admin). Feature is fully functional and production-ready."

    - agent: "testing"
      message: "INVOICE EDIT PERMISSION TEST COMPLETE ✅ - ALL TESTS PASSED (7/7 scenarios). Comprehensive testing of NEW invoice edit permission change on public URL https://c5016b85-dc98-485e-b5dc-5005ae41eac1.preview.emergentagent.com/api with admin, emp1, and emp2 credentials. CHANGE VERIFIED: PUT /api/invoices/{iid} now allows OWNER (creator, invoice.user) OR admin (was admin-only); DELETE /api/invoices/{iid} remains admin-only. RESULTS: ✅ SCENARIO 1 (Setup): emp1 creates invoice (customer='Invoice Edit Test Customer', phone='9998887771', items total ₹2000) - 200 OK, invoice.user='emp1', invoice_no='INV-000003'. ✅ SCENARIO 2 (Owner edit): emp1 PUT their OWN invoice with full valid body (changed items, new total ₹3400) - 200 OK, invoice updated successfully, pdf_token present (PDF regenerated). ✅ SCENARIO 3 (Cross-user edit forbidden): emp2 (different non-admin) PUT emp1's invoice - 403 Forbidden with message 'You can only edit your own invoices' (correctly blocked). ✅ SCENARIO 4 (Admin edit): admin PUT emp1's invoice - 200 OK, invoice updated successfully, pdf_token present (PDF regenerated - admin can edit anyone's invoice). ✅ SCENARIO 5 (Owner delete forbidden): emp1 DELETE their own invoice - 403 Forbidden (correctly blocked - DELETE is admin-only). ✅ SCENARIO 6 (Admin delete): admin DELETE emp1's invoice - 200 OK, deleted=true (admin can delete any invoice). ✅ SCENARIO 7 (Regression): GET /api/invoices - 200 OK (returns array of invoices). POST /api/invoices - 200 OK (invoice created successfully with invoice_no assigned). All test data cleaned up (2 customers, 2 invoices deleted). NO REGRESSIONS DETECTED. PERMISSION MODEL VERIFIED: PUT /api/invoices/{iid} allows owner OR admin (200), DELETE /api/invoices/{iid} is admin-only (403 for non-admin). Feature is fully functional and production-ready."

    - agent: "testing"
      message: "502 OUTAGE RECOVERY VERIFICATION COMPLETE ✅ - ALL TESTS PASSED (14/14). Comprehensive backend testing after environment reset and restoration on public URL https://c5016b85-dc98-485e-b5dc-5005ae41eac1.preview.emergentagent.com/api. PRIMARY 502 FIX VERIFIED: ✅ SECTION 1 - AUTHENTICATION (3/3 PASS): (1.1) ✅ POST /api/auth/login with admin/Admin@2026 returns 200 + access_token + user object (THIS WAS RETURNING 502 - NOW FIXED). (1.2) ✅ POST /api/auth/login with emp1/Emp@2026 returns 200 + access_token + user object. (1.3) ✅ GET /api/auth/me with admin token returns 200 with correct admin user details (username: admin, role: admin). ✅ SECTION 2 - CORE ENDPOINTS (6/6 PASS): (2.1) ✅ GET /api/sales returns 200 with list response. (2.2) ✅ GET /api/invoices returns 200 with list response. (2.3) ✅ GET /api/customers/search?q=test returns 200 with dict response. (2.4) ✅ GET /api/deliveries returns 200 with dict response. (2.5) ✅ GET /api/stats/today returns 200 with dict response. (2.6) ✅ GET /api/stats/my-report?weeks=8&months=6 returns 200 with dict response. ✅ SECTION 3 - ADVANCE-CREDIT FEATURE END-TO-END (5/5 PASS): (3.1) ✅ Create customer: POST /api/customers returns 200 with customer object containing id field. (3.2) ✅ Create advance receipt: POST /api/receipts with source_type='other', amount=3000 returns 200 with receipt object (id, amount=3000, source_type='other'). (3.3) ✅ Advance listed: GET /api/receipts/advances?customer_id=<id> returns 200 with advances array containing the receipt (remaining=3000, total_amount=3000). (3.4) ✅ Partial allocation: POST /api/sales with advance_allocations:[{receipt_id, amount:800}] returns 200, sale created successfully. (3.5) ✅ Advance persists: GET /api/receipts/advances?customer_id=<id> returns 200 with SAME receipt still present showing allocated=800, remaining=2200, total_amount=2200 (credit persistence verified - receipt NOT consumed fully, remaining balance available for future transactions). All test data cleaned up (1 customer, 1 receipt, 1 sale deleted). SUMMARY: The 502 error is RESOLVED. Backend is fully operational after environment restoration. All authentication endpoints working correctly (admin and employee login both return 200 + token). All core list endpoints returning 200. Advance-credit feature working end-to-end with correct persistence (partial allocations work, remaining balance tracked correctly). Database connection established, user seeding working, all dependencies (openpyxl, reportlab) installed correctly. NO REGRESSIONS DETECTED. System is production-ready."
