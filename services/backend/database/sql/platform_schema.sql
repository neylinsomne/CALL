-- ============================================================
-- LEVEL 1: SUPABASE - PLATFORM / ORGANIZATIONAL DATA
-- ============================================================
-- Execute this SQL in the Supabase SQL editor (one-time setup)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------
-- ORGANIZATIONS
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    domain TEXT UNIQUE,
    plan_type TEXT NOT NULL DEFAULT 'basic'
        CHECK (plan_type IN ('basic', 'professional', 'enterprise')),
    max_agents INTEGER NOT NULL DEFAULT 5,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_organizations_domain ON organizations(domain);
CREATE INDEX IF NOT EXISTS idx_organizations_active ON organizations(is_active) WHERE is_active = TRUE;

-- -----------------------------------------------------------
-- ORGANIZATION SERVERS
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS organization_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    ip_address INET NOT NULL,
    hostname TEXT,
    region TEXT DEFAULT 'default',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_heartbeat TIMESTAMPTZ,
    server_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(org_id, ip_address)
);

CREATE INDEX IF NOT EXISTS idx_org_servers_org ON organization_servers(org_id);
CREATE INDEX IF NOT EXISTS idx_org_servers_active ON organization_servers(is_active) WHERE is_active = TRUE;

-- -----------------------------------------------------------
-- API TOKENS (encryption-ready)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    token_prefix TEXT NOT NULL,
    name TEXT,
    scope TEXT NOT NULL DEFAULT 'agent:read,agent:write'
        CHECK (scope <> ''),
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_tokens_org ON api_tokens(org_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_prefix ON api_tokens(token_prefix);
CREATE INDEX IF NOT EXISTS idx_api_tokens_active ON api_tokens(is_active) WHERE is_active = TRUE;

-- -----------------------------------------------------------
-- AGENT REGISTRATIONS
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    agent_type TEXT NOT NULL DEFAULT 'inbound'
        CHECK (agent_type IN ('inbound', 'outbound', 'hybrid')),
    status TEXT NOT NULL DEFAULT 'registered'
        CHECK (status IN ('registered', 'provisioned', 'active', 'suspended', 'decommissioned')),
    server_id UUID REFERENCES organization_servers(id) ON DELETE SET NULL,
    config_snapshot JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_reg_org ON agent_registrations(org_id);
CREATE INDEX IF NOT EXISTS idx_agent_reg_server ON agent_registrations(server_id);
CREATE INDEX IF NOT EXISTS idx_agent_reg_status ON agent_registrations(status);

-- -----------------------------------------------------------
-- TRAINING CONFIGS
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS training_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    model_type TEXT NOT NULL DEFAULT 'tts'
        CHECK (model_type IN ('tts', 'stt', 'llm', 'embedding')),
    parameters JSONB NOT NULL DEFAULT '{}',
    dataset_reference TEXT,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'queued', 'training', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_training_configs_org ON training_configs(org_id);
CREATE INDEX IF NOT EXISTS idx_training_configs_status ON training_configs(status);

-- -----------------------------------------------------------
-- AUTO-UPDATE TRIGGERS
-- -----------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_organizations_updated_at') THEN
        CREATE TRIGGER update_organizations_updated_at
            BEFORE UPDATE ON organizations
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_org_servers_updated_at') THEN
        CREATE TRIGGER update_org_servers_updated_at
            BEFORE UPDATE ON organization_servers
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_agent_reg_updated_at') THEN
        CREATE TRIGGER update_agent_reg_updated_at
            BEFORE UPDATE ON agent_registrations
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_training_configs_updated_at') THEN
        CREATE TRIGGER update_training_configs_updated_at
            BEFORE UPDATE ON training_configs
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END
$$;
