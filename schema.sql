-- CRM Leads Database Schema
-- This file creates the necessary tables and sample data for the CRM application

-- Drop existing table if it exists
DROP TABLE IF EXISTS leads;

-- Create leads table
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    company VARCHAR(255),
    title VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'new',
    source VARCHAR(100),
    value DECIMAL(12, 2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_contacted_at TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_source ON leads(source);
CREATE INDEX idx_leads_company ON leads(company);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);

-- Insert sample data
INSERT INTO leads (name, email, phone, company, title, status, source, value, notes) VALUES
('John Smith', 'john.smith@example.com', '+1-555-0101', 'TechCorp', 'CTO', 'new', 'website', 50000.00, 'Interested in enterprise plan'),
('Sarah Johnson', 'sarah.j@techstartup.io', '+1-555-0102', 'TechStartup', 'CEO', 'contacted', 'linkedin', 75000.00, 'Met at conference'),
('Michael Brown', 'm.brown@innovate.co', '+1-555-0103', 'Innovate Co', 'VP Engineering', 'qualified', 'referral', 100000.00, 'Ready for demo'),
('Emily Davis', 'emily.d@growthlab.com', '+1-555-0104', 'GrowthLab', 'Founder', 'proposal', 'website', 45000.00, 'Waiting for contract review'),
('David Wilson', 'd.wilson@megacorp.com', '+1-555-0105', 'MegaCorp', 'Director of IT', 'negotiation', 'cold_call', 200000.00, 'Enterprise deal'),
('Lisa Anderson', 'lisa.a@cloudtech.io', '+1-555-0106', 'CloudTech', 'CTO', 'new', 'website', 80000.00, 'Downloaded whitepaper'),
('James Taylor', 'j.taylor@dataflow.com', '+1-555-0107', 'DataFlow', 'Lead Developer', 'contacted', 'github', 35000.00, 'Open source contributor'),
('Amanda Martinez', 'a.martinez@scaleup.co', '+1-555-0108', 'ScaleUp', 'COO', 'qualified', 'referral', 150000.00, 'Referred by existing customer'),
('Robert Chen', 'r.chen@nextlevel.com', '+1-555-0109', 'NextLevel', 'CEO', 'proposal', 'conference', 120000.00, 'Follow up next week'),
('Jennifer White', 'j.white@fastgrowth.io', '+1-555-0110', 'FastGrowth', 'VP Sales', 'new', 'website', 60000.00, 'Requested pricing'),
('Chris Lee', 'c.lee@enterprise.com', '+1-555-0111', 'Enterprise Inc', 'CIO', 'contacted', 'linkedin', 250000.00, 'Looking for solution'),
('Michelle Garcia', 'm.garcia@startup.com', '+1-555-0112', 'StartupCo', 'Founder', 'qualified', 'accelerator', 90000.00, 'Part of YC batch'),
('Daniel Thompson', 'd.thompson@bigtech.com', '+1-555-0113', 'BigTech', 'Engineering Manager', 'negotiation', 'referral', 180000.00, 'Finalizing terms'),
('Sarah Kim', 's.kim@innovate.io', '+1-555-0114', 'Innovate.io', 'CTO', 'new', 'blog', 55000.00, 'Read our blog post'),
('Andrew Rodriguez', 'a.rodriguez@techsol.com', '+1-555-0115', 'TechSol', 'CEO', 'proposal', 'cold_call', 95000.00, 'Sent proposal yesterday'),
('Nicole Adams', 'n.adams@cloudnine.com', '+1-555-0116', 'CloudNine', 'VP Engineering', 'contacted', 'conference', 110000.00, 'Met at TechConf'),
('Kevin Nelson', 'k.nelson@datacorp.com', '+1-555-0117', 'DataCorp', 'Director', 'qualified', 'website', 130000.00, 'Comparing with competitors'),
('Laura Hill', 'l.hill@scale.io', '+1-555-0118', 'Scale.io', 'COO', 'new', 'linkedin', 70000.00, 'Connected on LinkedIn'),
('Matthew Scott', 'm.scott@fasttrack.com', '+1-555-0119', 'FastTrack', 'Founder', 'negotiation', 'referral', 160000.00, 'Close to closing'),
('Jessica Green', 'j.green@techstar.com', '+1-555-0120', 'TechStar', 'CTO', 'proposal', 'website', 85000.00, 'Reviewing technical docs'),
('Ryan Hall', 'r.hall@growthco.io', '+1-555-0121', 'GrowthCo', 'VP Product', 'contacted', 'blog', 65000.00, 'Interested in features'),
('Stephanie Clark', 's.clark@enterprise.io', '+1-555-0122', 'Enterprise.io', 'CISO', 'qualified', 'conference', 220000.00, 'Security-focused discussion'),
('Joshua Lewis', 'j.lewis@techone.com', '+1-555-0123', 'TechOne', 'CEO', 'new', 'cold_call', 140000.00, 'Initial outreach made'),
('Amy Young', 'a.young@cloudsys.com', '+1-555-0124', 'CloudSys', 'VP Engineering', 'proposal', 'referral', 105000.00, 'Technical demo scheduled'),
('Brandon Wright', 'b.wright@dataflow.io', '+1-555-0125', 'DataFlow.io', 'CTO', 'negotiation', 'linkedin', 175000.00, 'Discussing SLA terms'),
('Sandra Lopez', 's.lopez@scalable.com', '+1-555-0126', 'Scalable', 'COO', 'contacted', 'website', 95000.00, 'Requested more information'),
('Gregory King', 'g.king@techtiger.com', '+1-555-0127', 'TechTiger', 'Founder', 'new', 'github', 40000.00, 'Starred our repo'),
('Diana Baker', 'd.baker@cloudify.com', '+1-555-0128', 'Cloudify', 'VP Sales', 'qualified', 'conference', 135000.00, 'Met at sales conference'),
('Christopher Bennett', 'c.bennett@techone.io', '+1-555-0129', 'TechOne.io', 'Director of IT', 'proposal', 'referral', 115000.00, 'Warm introduction');

-- Update some timestamps to simulate realistic data
UPDATE leads SET created_at = CURRENT_TIMESTAMP - INTERVAL '7 days' WHERE id IN (1, 2, 3, 4, 5);
UPDATE leads SET created_at = CURRENT_TIMESTAMP - INTERVAL '3 days' WHERE id IN (6, 7, 8, 9, 10);
UPDATE leads SET created_at = CURRENT_TIMESTAMP - INTERVAL '1 day' WHERE id IN (11, 12, 13, 14, 15);
UPDATE leads SET created_at = CURRENT_TIMESTAMP - INTERVAL '12 hours' WHERE id IN (16, 17, 18, 19, 20);
UPDATE leads SET created_at = CURRENT_TIMESTAMP - INTERVAL '6 hours' WHERE id IN (21, 22, 23, 24, 25);
UPDATE leads SET created_at = CURRENT_TIMESTAMP - INTERVAL '2 hours' WHERE id IN (26, 27, 28, 29, 30);

-- Add last_contacted_at for some leads
UPDATE leads SET last_contacted_at = CURRENT_TIMESTAMP - INTERVAL '2 days' WHERE id IN (2, 7, 12);
UPDATE leads SET last_contacted_at = CURRENT_TIMESTAMP - INTERVAL '5 hours' WHERE id IN (4, 9, 14);
UPDATE leads SET last_contacted_at = CURRENT_TIMESTAMP - INTERVAL '30 minutes' WHERE id IN (16, 21, 26);

-- Display summary
SELECT 'Leads table created successfully!' as message;
SELECT COUNT(*) as total_leads FROM leads;
SELECT status, COUNT(*) as count FROM leads GROUP BY status ORDER BY count DESC;
SELECT source, COUNT(*) as count FROM leads GROUP BY source ORDER BY count DESC;
