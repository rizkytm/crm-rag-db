# >ê Testing Guide for CRM Leads Assistant

## Table of Contents
1. [Pre-Test Setup](#pre-test-setup)
2. [Testing User Roles](#testing-user-roles)
3. [Testing Security Features](#testing-security-features)
4. [Testing SQL Queries](#testing-sql-queries)
5. [Testing UI Components](#testing-ui-components)
6. [Test Scenarios](#test-scenarios)
7. [Expected Results by Role](#expected-results-by-role)
8. [Troubleshooting Tests](#troubleshooting-tests)

---

## Pre-Test Setup

### 1. Start the Application

```bash
cd /Users/rizkytm/Documents/playground/awesome-llm-apps/crm-rag-db
venv/bin/streamlit run app_secure.py
```

The app will open at: `http://localhost:8501`

### 2. Verify Database Connection

Before testing, ensure the database is accessible:

```bash
# Check if PostgreSQL container is running
docker ps | grep crm_postgres

# Test database connection
docker exec -it crm_postgres psql -U postgres -d crm_db_rag -c "SELECT COUNT(*) FROM leads;"
# Should return: 30
```

### 3. Verify Demo Users

Check that all test users exist:

```bash
docker exec -it crm_postgres psql -U postgres -d crm_db_rag -c "SELECT username, r.name as role FROM users u JOIN roles r ON u.role_id = r.id;"
```

Expected output:
```
 username |   role
----------|----------
 admin    | admin
 manager  | manager
 sales    | sales_rep
 viewer   | viewer
```

---

## Testing User Roles

### Test 1: Administrator (admin)

**Login:**
- Username: `admin`
- Password: (any)

**Expected Capabilities:**
-  See ALL 30 leads
-  View ALL columns (name, email, company, status, source, value, etc.)
-  View internal notes and admin notes
-  Access audit logs
-  Export data
-  Run any SQL query without restrictions

**UI Elements to Verify:**
- =Q Administrator badge in header
- < Team Access indicator
-  All permissions shown in green in sidebar
- =Ë Audit Log viewer button in sidebar

**Test Queries:**
```
1. "Show me all leads" ’ Should return 30 leads
2. "Who is Diana Baker?" ’ Should find her (ID: 2)
3. "Show me leads by status" ’ Should show all statuses
4. "What's the total value of all deals?" ’ Should show total value
5. "Show me internal notes" ’ Should display notes
```

### Test 2: Manager (manager)

**Login:**
- Username: `manager`
- Password: (any)

**Expected Capabilities:**
-  See ALL 30 leads (team data)
-  View deal value column
-   Internal notes HIDDEN
-   Admin notes HIDDEN
-  Run team statistics
-  Export data

**UI Elements to Verify:**
- <÷ Role: manager badge
- < Team Access indicator
-  View team leads (green)
-   Internal notes hidden (yellow)
- L No audit log viewer

**Test Queries:**
```
1. "Show me all leads" ’ Should return 30 leads
2. "Leads by status" ’ Should show team statistics
3. "Show me latest leads with value" ’ Should show value column
4. "Show me internal notes" ’ Should NOT show notes (column filtered)
```

### Test 3: Sales Representative (sales)

**Login:**
- Username: `sales`
- Password: (any)

**Expected Capabilities:**
- L Only 16 assigned leads (not all 30)
- L Deal value HIDDEN
- L Internal notes HIDDEN
- L Cannot export
-  Can update own leads
- = All queries auto-filtered

**UI Elements to Verify:**
- = Personal Access indicator
- = Security notice: "You can only view your assigned leads"
- L Only assigned leads (red)
- L Deal value hidden (red)
- L Cannot export (red)

**Test Queries:**
```
1. "Show me all leads" ’ Should only show 16 assigned leads
2. "Show me latest leads" ’ Should show only their 16 leads
3. "Leads with highest value" ’ Should return empty (value column hidden)
4. "My leads by status" ’ Should show stats for their 16 leads
```

**Verify Assigned Leads:**
```bash
docker exec -it crm_postgres psql -U postgres -d crm_db_rag -c "
SELECT COUNT(DISTINCT l.id)
FROM leads l
WHERE l.owner_id = 3
   OR l.id IN (SELECT lead_id FROM lead_assignments WHERE user_id = 3);
"
# Should return: 16
```

### Test 4: Viewer (viewer)

**Login:**
- Username: `viewer`
- Password: (any)

**Expected Capabilities:**
- L Only assigned leads (~5-9 leads)
- L Deal value HIDDEN
- L Read-only (no modifications)
- L Cannot export
- = All queries auto-filtered

**UI Elements to Verify:**
- = Personal Access indicator
- = Security notice visible
- L Only assigned leads (red)
- L Read-only (red)
- L Cannot export (red)

**Test Queries:**
```
1. "Show me my leads" ’ Should show only assigned leads
2. "Leads by status" ’ Should show only their leads
```

---

## Testing Security Features

### Test 1: Row-Level Security (Data Isolation)

**Objective:** Verify users can only see their assigned leads

**Steps:**
1. Login as `sales`
2. Run: "Show me all leads"
3. Count the results
4. Logout and login as `admin`
5. Run: "Show me all leads"
6. Count the results

**Expected:**
- Sales: 16 leads
- Admin: 30 leads

**Verification Query:**
```bash
docker exec -it crm_postgres psql -U postgres -d crm_db_rag -c "
-- Check sales user's assigned leads
SELECT COUNT(*) FROM (
  SELECT DISTINCT l.id
  FROM leads l
  WHERE l.owner_id = 3
     OR l.id IN (SELECT lead_id FROM lead_assignments WHERE user_id = 3)
) AS sales_leads;
"
```

### Test 2: Column-Level Security (Data Hiding)

**Objective:** Verify sensitive columns are hidden for non-admins

**Steps:**
1. Login as `admin`
2. Run: "SELECT * FROM leads LIMIT 5"
3. Note all columns visible (including `value`, `internal_notes`)
4. Logout and login as `sales`
5. Run: "SELECT * FROM leads LIMIT 5"
6. Verify `value` column is NOT in results

**Expected:**
- Admin: All columns visible
- Sales: No `value`, `internal_notes`, or `admin_notes` columns

### Test 3: Query Sanitization

**Objective:** Verify queries are automatically modified for security

**Steps:**
1. Enable SQL logging in auth.py (temporary)
2. Login as `sales`
3. Run: "SELECT * FROM leads"
4. Check the logs for the modified query

**Expected Query Transformation:**

**Original:**
```sql
SELECT * FROM leads ORDER BY created_at DESC LIMIT 10
```

**Modified for Sales (user_id=3):**
```sql
SELECT id, name, email, phone, company, title, status, source, notes, created_at, updated_at
FROM leads
WHERE (id IN (SELECT lead_id FROM lead_assignments WHERE user_id = 3) OR owner_id = 3)
ORDER BY created_at DESC
LIMIT 10
```

**Key Changes:**
- `*` replaced with specific columns (no `value`)
- WHERE clause added: filters by user assignments

### Test 4: Audit Logging

**Objective:** Verify all data access is logged

**Steps:**
1. Login as `admin`
2. Run several queries
3. In sidebar, click "Show Recent Activity"
4. Verify all queries appear in audit log

**Expected Log Columns:**
- action: 'query', 'view_my_leads', etc.
- username: 'admin'
- table_name: 'leads'
- created_at: timestamp

**Verification Query:**
```bash
docker exec -it crm_postgres psql -U postgres -d crm_db_rag -c "
SELECT
    al.action,
    u.username,
    al.table_name,
    al.created_at
FROM audit_logs al
JOIN users u ON al.user_id = u.id
ORDER BY al.created_at DESC
LIMIT 10;
"
```

---

## Testing SQL Queries

### Basic Queries

**Test 1: Simple SELECT**
```
Query: "Show me 5 latest leads"
Expected: 5 leads ordered by created_at DESC
Columns: id, name, email, company, status, source, created_at
```

**Test 2: WHERE clause**
```
Query: "Show me leads from website"
Expected: Leads where source = 'website'
```

**Test 3: Aggregation**
```
Query: "Count leads by status"
Expected: Table with status and count columns
```

**Test 4: JOIN**
```
Query: "Show me leads with user assignments"
Expected: Results from leads joined with lead_assignments
```

### Advanced Queries

**Test 5: GROUP BY + HAVING**
```
Query: "Show me sources with more than 5 leads"
Expected: Sources grouped, filtered by COUNT > 5
```

**Test 6: ORDER BY**
```
Query: "Show me leads by value descending"
Admin: Should show value column
Sales: Should fail (value column hidden)
```

**Test 7: Date filtering**
```
Query: "Show me leads created in the last 7 days"
Expected: Recent leads only
```

### Edge Cases

**Test 8: Empty result**
```
Query: "Show me leads from unknown_source"
Expected: "No results found" message
```

**Test 9: Invalid SQL**
```
Query: "SHOW TABLES" (MySQL syntax)
Expected: Error message with helpful hint
```

**Test 10: Permission denied**
```
Query (as sales): "SELECT value FROM leads"
Expected: Error or empty results (column sanitized)
```

---

## Testing UI Components

### Test 1: Login Page

**Verify:**
-  Page title: "= CRM Leads Assistant"
-  Login form with username and password fields
-  Demo accounts table displayed correctly
-  Form validation (empty fields show error)
-  Invalid credentials show error message

**Test Cases:**
1. Empty username + password ’ "Please enter both username and password"
2. Invalid username ’ "Invalid username or password"
3. Valid credentials ’ Redirects to main app

### Test 2: Main App Header

**Verify (per role):**
- =d User full name displayed
- <÷ Role badge shown
- </= Access level indicator
- =Q Admin badge (admin only)
- =ª Logout button works

**Test:** Click logout ’ Returns to login page, session cleared

### Test 3: Sidebar

**Verify:**
- User name and role shown
- Permissions checklist (/L/ )
- Quick stats metric updates correctly
- Example queries displayed
- Audit log viewer (admin only)

**Test Cases:**
1. Admin login ’ All  green checks
2. Sales login ’ Mix of L red and   yellow
3. Click "Show Recent Activity" (admin) ’ Audit log displays

### Test 4: Query Interface

**Verify:**
- Text area with placeholder text
- Search button with primary styling
- Form submission works
- Results display in markdown format
- Loading spinner shows during query execution

**Known Behavior:**
- Cmd+Enter not supported (Streamlit limitation)
- Click button or use Tab + Enter

### Test 5: Quick Action Buttons

**Verify:**
- All 4 buttons display correctly
- Buttons execute queries on click
- Results appear below buttons
- "Team Overview" only shows for admin/manager
- "My New Leads" shows for sales/viewer

**Test Cases:**
1. Click "=Ê My Latest Leads" ’ Shows 10 latest
2. Click "=È My Leads by Status" ’ Shows status counts
3. Click "<â My Leads by Source" ’ Shows source counts
4. Click "=e Team Overview" (admin) ’ Shows all team stats

### Test 6: Results Display

**Verify:**
- Results section header: "=Ë Results"
- Tables render with proper formatting
- No more than 20 rows shown (with "... and X more rows" message)
- Security notice appears for non-admins: "= Showing only your assigned leads"

---

## Test Scenarios

### Scenario 1: Data Isolation Verification

**Purpose:** Confirm users cannot see other users' data

**Steps:**
1. Login as `sales`
2. Query: "Show me all leads"
3. Save results (should be 16 leads)
4. Logout
5. Login as `admin`
6. Query: "Show me all leads"
7. Save results (should be 30 leads)
8. Compare: Admin sees 14 more leads than sales

**Expected:**
- Sales user: 16 leads (IDs: varies, check assignments)
- Admin: 30 leads (all leads in database)

### Scenario 2: Data Leak Prevention

**Purpose:** Ensure sensitive financial data is protected

**Steps:**
1. Login as `admin`
2. Query: "SELECT * FROM leads LIMIT 5"
3. Verify `value` column shows amounts like "$50,000", "$100,000"
4. Logout
5. Login as `sales`
6. Query: "SELECT * FROM leads LIMIT 5"
7. Verify `value` column is NOT in results
8. Query: "Show me total deal value"
9. Verify error or no results (column not accessible)

**Expected:**
- Admin: Can see financial data
- Sales: Cannot see or query financial data

### Scenario 3: Audit Trail Completeness

**Purpose:** Verify compliance logging

**Steps:**
1. Login as `sales`
2. Run 5 different queries
3. Logout
4. Login as `admin`
5. Click "Show Recent Activity" in sidebar
6. Verify all 5 queries from sales user are logged
7. Check timestamps are accurate

**Expected:**
- Every query logged with:
  - User ID
  - Action type
  - Table name
  - Query text (first 1000 chars)
  - Timestamp

### Scenario 4: Role-Based Feature Access

**Purpose:** Test permission boundaries

**Steps:**
1. Create a matrix of features to test
2. Test each feature as each user role
3. Document access/denial

**Feature Matrix:**
| Feature | Admin | Manager | Sales | Viewer |
|---------|-------|---------|-------|--------|
| View all leads |  |  | L | L |
| See deal value |  |  | L | L |
| See notes |  |   | L | L |
| Export data |  |  | L | L |
| View audit logs |  | L | L | L |

### Scenario 5: Concurrent User Sessions

**Purpose:** Verify session isolation

**Steps:**
1. Open browser in Incognito window 1
2. Login as `admin`
3. Note the leads visible
4. Open browser in Incognito window 2
5. Login as `sales`
6. Note the leads visible (should be fewer)
7. Run a query in window 1 (admin)
8. Run a query in window 2 (sales)
9. Verify results are different per user

**Expected:**
- Sessions properly isolated
- No data leakage between sessions

---

## Expected Results by Role

### Administrator (admin) - Reference Data

**Total Leads:** 30

**Sample Lead (Diana Baker):**
```json
{
  "id": 2,
  "name": "Diana Baker",
  "email": "diana.baker@cloudify.com",
  "company": "Cloudify",
  "status": "qualified",
  "source": "website",
  "value": "$75,000",
  "notes": "Interested in enterprise plan",
  "internal_notes": "Vip customer - priority handling",
  "created_at": "2025-01-02 10:30:00"
}
```

**All Columns Visible:**
- id, name, email, phone, company, title, status, source, value, notes, internal_notes, admin_notes, created_at, updated_at, last_contacted_at

**Can Access:**
-  All 30 leads
-  Deal values
-  Internal notes
-  Admin notes
-  Audit logs
-  Any SQL query

### Manager (manager) - Reference Data

**Total Leads:** 30 (same as admin)

**Columns Visible:**
- All columns EXCEPT: internal_notes, admin_notes

**Can Access:**
-  All 30 leads
-  Deal values
- L Internal notes
- L Admin notes
- L Audit logs
-  Team statistics

### Sales Rep (sales) - Reference Data

**Total Leads:** 16 (assigned only)

**Assigned Lead IDs:**
- Owner: 5 leads (IDs vary)
- Assigned via lead_assignments: 10-12 leads

**Sample Result:**
```
Query returned 16 row(s):

| id | name | email | company | status | source | created_at |
|----|------|-------|---------|--------|--------|------------|
| 1  | John Smith | john@techcorp.com | TechCorp | new | website | 2025-01-01 |
...
(16 rows total)
```

**Columns Visible:**
- id, name, email, phone, company, title, status, source, notes, created_at, updated_at
- L value (hidden)
- L internal_notes (hidden)
- L admin_notes (hidden)

**Can Access:**
- L Only 16 assigned leads
- L No deal values
- L No internal notes
- L Cannot export
-  Update own leads

### Viewer (viewer) - Reference Data

**Total Leads:** 5-9 (assigned only)

**Can Access:**
- L Only assigned leads
- L Read-only
- L No sensitive data
- L Cannot export

---

## Troubleshooting Tests

### Issue 1: "Invalid username or password"

**Possible Causes:**
1. Demo users not created in database
2. Typo in username
3. Database connection issue

**Solutions:**
```bash
# Check if users exist
docker exec -it crm_postgres psql -U postgres -d crm_db_rag -c "SELECT username FROM users;"

# Recreate demo users if missing
docker exec -it crm_postgres psql -U postgres -d crm_db_rag -f security_schema.sql
```

### Issue 2: "No leads assigned to you" (for sales user)

**Possible Causes:**
1. Sales user has no leads assigned
2. owner_id or lead_assignments not set

**Solutions:**
```bash
# Check sales user ID
docker exec -it crm_postgres psql -U postgres -d crm_db_rag -c "SELECT id, username FROM users WHERE username = 'sales';"

# Check assigned leads count
docker exec -it crm_postgres psql -U postgres -d crm_db_rag -c "
SELECT COUNT(DISTINCT l.id)
FROM leads l
WHERE l.owner_id = 3
   OR l.id IN (SELECT lead_id FROM lead_assignments WHERE user_id = 3);
"

# Assign leads if needed
docker exec -it crm_postgres psql -U postgres -d crm_db_rag -c "
INSERT INTO lead_assignments (lead_id, user_id, assigned_at)
SELECT id, 3, NOW()
FROM leads
WHERE id IN (1,2,3,4,5)
ON CONFLICT DO NOTHING;
"
```

### Issue 3: Agent can't find specific lead

**Example:** "Who is Diana Baker?" ’ Agent says can't find

**Possible Causes:**
1. Agent using wrong tool (my_leads instead of execute_sql)
2. User doesn't have access to that lead
3. Lead doesn't exist

**Solutions:**
1. Use specific query: "Show me lead named Diana Baker"
2. Check if user has access to that lead
3. As admin, use: "SELECT * FROM leads WHERE name LIKE '%Diana%'"

### Issue 4: SQL syntax error in queries

**Example Error:** "argument of AND must be type boolean"

**Possible Causes:**
1. WHERE clause not properly wrapped
2. Sanitization logic error

**Solutions:**
- Check auth.py sanitize_query() method
- Ensure WHERE clauses wrap OR conditions in parentheses
- Test query directly in database first

### Issue 5: Query works but results delayed

**Possible Causes:**
1. Large result set
2. Database connection pool exhausted
3. Agent processing time

**Solutions:**
1. Add LIMIT clause to queries
2. Check database performance
3. Monitor agent response time

### Issue 6: Audit log not showing entries

**Possible Causes:**
1. Audit log table doesn't exist
2. Logging failing silently
3. User not admin (can't view logs)

**Solutions:**
```bash
# Check audit_logs table exists
docker exec -it crm_postgres psql -U postgres -d crm_db_rag -c "\d audit_logs"

# Check recent logs
docker exec -it crm_postgres psql -U postgres -d crm_db_rag -c "
SELECT COUNT(*) FROM audit_logs;
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 5;
"
```

### Issue 7: Changes not visible after code update

**Possible Causes:**
1. Streamlit caching
2. Browser cache
3. Not using --force-run

**Solutions:**
```bash
# Clear Streamlit cache
rm -rf ~/.streamlit/cache/

# Restart with clear cache
venv/bin/streamlit run app_secure.py --logger.level=debug

# Hard refresh browser
Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
```

---

## Quick Test Checklist

Use this checklist for quick smoke testing before deployment:

### Basic Functionality
- [ ] App starts without errors
- [ ] Login page loads
- [ ] Can login as admin
- [ ] Can login as sales
- [ ] Can logout successfully

### Core Features
- [ ] Admin sees all 30 leads
- [ ] Sales sees only assigned leads
- [ ] Admin can see deal values
- [ ] Sales cannot see deal values
- [ ] Query execution works
- [ ] Results display correctly

### Security
- [ ] Row-level filtering works
- [ ] Column-level filtering works
- [ ] Audit logs are created
- [ ] Admin can view audit logs
- [ ] Sales cannot view audit logs

### UI Components
- [ ] All buttons clickable
- [ ] Sidebar displays permissions
- [ ] Quick stats update
- [ ] Quick action buttons work
- [ ] Results format nicely

### Edge Cases
- [ ] Empty query shows warning
- [ ] Invalid query shows error
- [ ] No results shows message
- [ ] Large result set truncates to 20 rows
- [ ] Special characters in queries work

---

## Performance Testing

### Test 1: Query Response Time

**Objective:** Ensure queries complete in reasonable time

**Steps:**
1. Login as admin
2. Run: "SELECT * FROM leads"
3. Measure time to results
4. Repeat 5 times, calculate average

**Expected:**
- Simple queries: < 2 seconds
- Complex queries: < 5 seconds
- Aggregation queries: < 3 seconds

### Test 2: Concurrent User Load

**Objective:** Test system under multiple users

**Steps:**
1. Open 5 browser windows
2. Login as different users in each
3. Run queries simultaneously
4. Monitor for errors or slowdowns

**Expected:**
- No errors
- Acceptable response time (< 10 seconds)
- No data leakage between sessions

---

## Security Testing

### Test 1: SQL Injection Prevention

**Attempt:** Try to inject SQL through query input

```
Test input: "'; DROP TABLE leads; --"
Expected: Query fails safely, no damage
```

```
Test input: "1' OR '1'='1"
Expected: Sanitized or rejected
```

### Test 2: Cross-User Data Access

**Attempt:** Access another user's data

```
1. Login as sales
2. Query: "SELECT * FROM leads WHERE id = 1" (unassigned lead)
Expected: No results (filtered by WHERE clause)
```

### Test 3: Session Hijacking Prevention

**Attempt:** Access app without login

```
1. Clear browser cookies
2. Navigate to http://localhost:8501
Expected: Redirected to login page
```

---

## Conclusion

This testing guide covers all major aspects of the CRM Leads Assistant:
-  User role testing
-  Security feature verification
-  SQL query testing
-  UI component testing
-  Real-world scenarios
-  Troubleshooting common issues

**Remember:**
- Test thoroughly before deploying to production
- Document any deviations from expected results
- Keep audit logs for compliance
- Review permissions regularly

For additional help, refer to:
- README.md - Setup and installation
- SECURE_APP_GUIDE.md - Security features overview
- SECURITY.md - Security architecture
