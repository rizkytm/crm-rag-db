-- Security and Access Control Schema for CRM
-- Run this to add user management and role-based access control

-- Create roles
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default roles
INSERT INTO roles (name, description) VALUES
('admin', 'Full access to all leads and system settings'),
('manager', 'Access to team leads and reports'),
('sales_rep', 'Access only to assigned leads'),
('viewer', 'Read-only access to assigned leads')
ON CONFLICT (name) DO NOTHING;

-- Create users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create lead assignments (which user can see which lead)
CREATE TABLE IF NOT EXISTS lead_assignments (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES users(id),
    UNIQUE(lead_id, user_id)
);

-- Create audit log
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL, -- 'view', 'export', 'query', etc.
    table_name VARCHAR(100),
    record_ids TEXT, -- JSON array of affected record IDs
    query_text TEXT, -- The actual SQL query executed
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add user_id column to leads table (to track ownership)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES users(id);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(id);

-- Add indexes for security queries
CREATE INDEX IF NOT EXISTS idx_leads_owner ON leads(owner_id);
CREATE INDEX IF NOT EXISTS idx_lead_assignments_lead ON lead_assignments(lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_assignments_user ON lead_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);

-- Enable Row Level Security (optional, for PostgreSQL)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Create policy for admins (can see all)
DROP POLICY IF EXISTS admin_all_leads ON leads;
CREATE POLICY admin_all_leads ON leads
    FOR ALL
    TO (SELECT id FROM users WHERE username = 'admin')
    USING (true);

-- Insert sample users
INSERT INTO users (username, email, full_name, role_id) VALUES
('admin', 'admin@company.com', 'System Administrator', 1),
('john_manager', 'john@company.com', 'John Smith', 2),
('sarah_sales', 'sarah@company.com', 'Sarah Johnson', 3),
('mike_viewer', 'mike@company.com', 'Mike Brown', 4)
ON CONFLICT (username) DO NOTHING;

-- Assign some leads to users
-- Admin can see all, but let's assign specific leads to sales reps
INSERT INTO lead_assignments (lead_id, user_id)
SELECT l.id, u.id
FROM leads l
CROSS JOIN users u
WHERE u.username IN ('sarah_sales', 'john_manager')
AND l.id % 2 = 0  -- Assign every other lead
LIMIT 10
ON CONFLICT (lead_id, user_id) DO NOTHING;

-- Update leads with owner
UPDATE leads
SET owner_id = (SELECT id FROM users WHERE username = 'sarah_sales')
WHERE id % 3 = 0;

UPDATE leads
SET owner_id = (SELECT id FROM users WHERE username = 'john_manager')
WHERE id % 3 = 1;

-- Show summary
SELECT 'Security setup completed!' as message;
SELECT 'Users created:' as info, COUNT(*) as count FROM users;
SELECT 'Roles created:' as info, COUNT(*) as count FROM roles;
SELECT 'Lead assignments:' as info, COUNT(*) as count FROM lead_assignments;
