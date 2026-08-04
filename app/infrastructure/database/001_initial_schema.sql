CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'active',
    current_step TEXT NOT NULL DEFAULT 'greeting',
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id BIGSERIAL PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(conversation_id),
    patient_name TEXT NOT NULL,
    patient_phone TEXT,
    clinic_name TEXT NOT NULL,
    specialty TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_appointments_conversation_id
    ON appointments(conversation_id);
