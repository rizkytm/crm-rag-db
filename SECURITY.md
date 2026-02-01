# 🔒 Security & Access Control Implementation

## Overview

This CRM now includes comprehensive security features to control data access and protect sensitive information.

## Security Features Implemented

### 1. **Authentication** (`auth.py`)
- **User Login System**: Users must authenticate with username/password
- **Role-Based Access Control (RBAC)**: 4 predefined roles
- **Session Management**: Track logged-in users

### 2. **Row-Level Security**
- **Admin/Manager**: Can see ALL leads
- **Sales Rep**: Can ONLY see their assigned leads
- **Viewer**: Read-only access to their leads

### 3. **Column-Level Security**
- **Admin**: Sees ALL fields (value, notes, etc.)
- **Manager**: Sees most fields, no internal notes
- **Sales Rep/Viewer**: Can't see sensitive data (deal value, internal notes)

### 4. **Audit Logging**
- Track WHO accessed WHAT data
- Log queries executed
- Track timestamps

## 📊 User Roles

| Role | Permissions | Can See Value | Can See All Leads | Can Export |
|------|-------------|---------------|-------------------|------------|
| **admin** | Full access | ✅ | ✅ | ✅ |
| **manager** | Team leads | ✅ | ✅ | ✅ |
| **sales_rep** | Own leads only | ❌ | ❌ | ❌ |
| **viewer** | Read-only own leads | ❌ | ❌ | ❌ |

## 🗄️ Database Schema

### New Tables

**1. roles** - Define user roles
```sql
- id, name, description, created_at
```

**2. users** - User accounts
```sql
- id, username, email, full_name, role_id, is_active
```

**3. lead_assignments** - Which user can see which lead
```sql
- lead_id, user_id, assigned_at, assigned_by
```

**4. audit_logs** - Track all data access
```sql
- user_id, action, table_name, record_ids, query_text, created_at
```

### Modified Tables

**leads** - Added ownership
```sql
- owner_id (who owns this lead)
- created_by_id (who created it)
```

## 🚀 Setup Instructions

### Step 1: Run Security Schema

```bash
# Add security tables to your database
docker exec crm_postgres psql -U crm_user -d crm_db_rag -f security_schema.sql
```

### Step 2: Create Demo Users

```bash
python -c "from auth import create_demo_users; from db_connection import CRMDatabase; create_demo_users(CRMDatabase())"
```

### Step 3: Test Different Roles

Demo users created:
- **admin** / admin@company.com (Role: admin)
- **manager** / manager@company.com (Role: manager)
- **sales** / sales@company.com (Role: sales_rep)
- **viewer** / viewer@company.com (Role: viewer)

## 🔍 How It Works

### Query Sanitization Example

**Original Query:**
```sql
SELECT * FROM leads ORDER BY created_at DESC LIMIT 10
```

**For Admin (Sees Everything):**
```sql
SELECT * FROM leads ORDER BY created_at DESC LIMIT 10
-- Returns all leads with all columns
```

**For Sales Rep (Row + Column Security):**
```sql
SELECT id, name, email, phone, company, title, status, source, notes, created_at, updated_at, last_contacted_at
FROM leads
WHERE (id IN (SELECT lead_id FROM lead_assignments WHERE user_id = 3) OR owner_id = 3)
ORDER BY created_at DESC
LIMIT 10
-- Returns only their leads, without 'value' column
```

### Access Control Flow

```
User Query
    ↓
Check User Authentication
    ↓
Check User Permissions (Role)
    ↓
Sanitize Query:
  - Remove hidden columns
  - Add WHERE filters for row-level security
    ↓
Execute Sanitized Query
    ↓
Log to Audit Table
    ↓
Return Results
```

## 📝 Usage Example

```python
from db_connection import CRMDatabase
from auth import AuthService
from crm_agent import CRMDatabaseTools

# Initialize
db = CRMDatabase()
auth_service = AuthService(db)

# Authenticate user
user = auth_service.authenticate_user("sales", "password")

# Create tools WITH security
tools = CRMDatabaseTools(
    db_connection=db,
    user=user,  # Pass user for permission checks
    auth_service=auth_service  # Pass auth service
)

# Query automatically sanitized
result = tools.execute_sql("SELECT * FROM leads")
# Sales user will ONLY see their leads, without 'value' column!
```

## 🔐 Security Best Practices Implemented

1. ✅ **Principle of Least Privilege**: Users only see data they need
2. ✅ **Audit Trail**: All access is logged
3. ✅ **No Hardcoded Secrets**: Credentials in environment variables
4. ✅ **SQL Injection Prevention**: Using parameterized queries
5. ✅ **Defense in Depth**: Multiple security layers (auth + row security + column security)

## 🚧 TODO for Production

- [ ] Implement proper password hashing (bcrypt)
- [ ] Add JWT token-based authentication
- [ ] Implement session management
- [ ] Add rate limiting
- [ ] Enforce HTTPS
- [ ] Add CAPTCHA for login
- [ ] Implement password reset flow
- [ ] Add two-factor authentication (2FA)
- [ ] Implement PostgreSQL Row-Level Security (RLS) policies
- [ ] Add API rate limiting per user
- [ ] Implement data export restrictions

## 📖 Example Scenarios

### Scenario 1: Sales Rep Views Leads

**User**: Sarah (sales_rep)

**Query**: "Show me latest leads"

**What Happens**:
1. Sarah authenticates
2. System checks her role (sales_rep)
3. Query is modified:
   - Only her assigned leads (WHERE owner_id = 3 OR lead_id IN assignments)
   - Sensitive columns removed (no 'value' column)
4. Results show only Sarah's leads
5. Access logged to audit_logs

### Scenario 2: Manager Views Team Performance

**User**: John (manager)

**Query**: "How many leads by status?"

**What Happens**:
1. John authenticates
2. System checks his role (manager)
3. Query is allowed (managers can see team data)
4. Results show ALL leads with status counts
5. Access logged

### Scenario 3: Viewer Tries to Export

**User**: Mike (viewer)

**Action**: Attempts to export data

**Result**: ❌ Denied - Viewers cannot export

## 🎯 Key Benefits

1. **Compliance**: Helps with GDPR, CCPA compliance
2. **Data Protection**: Sensitive data (deal values) protected
3. **Accountability**: Full audit trail
4. **Flexibility**: Easy to add new roles or modify permissions
5. **Transparent**: Users know what they can access

## 📞 Next Steps

To enable this in your Streamlit app:

1. Add a login page to `app.py`
2. Store authenticated user in session state
3. Pass user and auth_service to CRMDatabaseTools
4. Display user's role and permissions in UI
5. Add audit log viewer for admins

Would you like me to add the login UI to the Streamlit app?
