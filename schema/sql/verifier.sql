CREATE TABLE email_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    domain TEXT NOT NULL,
    job_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    duration_seconds NUMERIC,
    dns JSONB,
    smtp JSONB,
    heuristics JSONB,
    scoring JSONB,
    status TEXT
);

CREATE INDEX idx_email_verifications_email ON email_verifications (email);
CREATE INDEX idx_email_verifications_domain ON email_verifications (domain);
CREATE INDEX idx_email_verifications_created_at ON email_verifications (created_at);
