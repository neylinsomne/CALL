-- ============================================================
-- LEVEL 2: LOCAL POSTGRESQL - AGENT OPERATIONAL DATA
-- ============================================================
-- Loaded automatically by Docker on first container creation

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- -----------------------------------------------------------
-- ORGANIZATIONS (local copy for self-contained operation)
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

-- -----------------------------------------------------------
-- API TOKENS (local, rotation every 90 days)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    token_prefix TEXT NOT NULL,
    name TEXT,
    scope TEXT NOT NULL DEFAULT 'agent:read,agent:write,calls:read,qa:read',
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_tokens_org ON api_tokens(org_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_prefix ON api_tokens(token_prefix);
CREATE INDEX IF NOT EXISTS idx_api_tokens_active ON api_tokens(is_active) WHERE is_active = TRUE;

-- -----------------------------------------------------------
-- VOICE PROFILES (must exist before agents)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS voice_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    model_name TEXT NOT NULL,
    language VARCHAR(10) NOT NULL DEFAULT 'es',
    sample_audio_path TEXT,
    parameters JSONB DEFAULT '{}',
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_voice_profiles_default
    ON voice_profiles(is_default) WHERE is_default = TRUE;

-- -----------------------------------------------------------
-- CONTEXT PROFILES (must exist before agents)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS context_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID,
    name TEXT NOT NULL DEFAULT 'default',
    system_prompt TEXT,
    personality TEXT,
    greeting_message TEXT,
    fallback_message TEXT,
    max_context_turns INTEGER DEFAULT 10,
    temperature FLOAT DEFAULT 0.7,
    parameters JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------
-- AGENTS (local instances)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    agent_registration_id UUID,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'idle'
        CHECK (status IN ('idle', 'active', 'busy', 'offline', 'error')),
    sip_port INTEGER,
    ws_port INTEGER,
    assigned_voice_id UUID REFERENCES voice_profiles(id) ON DELETE SET NULL,
    context_profile_id UUID REFERENCES context_profiles(id) ON DELETE SET NULL,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_org ON agents(org_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);

-- Add FK from context_profiles to agents
ALTER TABLE context_profiles
    ADD CONSTRAINT fk_context_profiles_agent
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_context_profiles_agent ON context_profiles(agent_id);

-- -----------------------------------------------------------
-- CONVERSATIONS (existing, enhanced with agent_id)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    caller_id VARCHAR(50),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_started ON conversations(started_at);
CREATE INDEX IF NOT EXISTS idx_conversations_agent ON conversations(agent_id);

-- -----------------------------------------------------------
-- MESSAGES (existing)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL,
    content TEXT NOT NULL,
    audio_path VARCHAR(255),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);

-- -----------------------------------------------------------
-- CALL LOGS (existing)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_logs_conversation ON call_logs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_call_logs_event_type ON call_logs(event_type);

-- -----------------------------------------------------------
-- VOICE ASSIGNMENTS
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS voice_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    voice_profile_id UUID NOT NULL REFERENCES voice_profiles(id) ON DELETE CASCADE,
    sip_port INTEGER,
    ws_sub_port INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(agent_id, voice_profile_id)
);

CREATE INDEX IF NOT EXISTS idx_voice_assignments_agent ON voice_assignments(agent_id);
CREATE INDEX IF NOT EXISTS idx_voice_assignments_active
    ON voice_assignments(is_active) WHERE is_active = TRUE;

-- -----------------------------------------------------------
-- RAG BATCHES
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    source_type TEXT NOT NULL DEFAULT 'file'
        CHECK (source_type IN ('file', 'url', 'api', 'database')),
    source_path TEXT,
    embedding_model TEXT DEFAULT 'all-MiniLM-L6-v2',
    vector_count INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'indexed', 'failed', 'archived')),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_batches_agent ON rag_batches(agent_id);
CREATE INDEX IF NOT EXISTS idx_rag_batches_status ON rag_batches(status);

-- -----------------------------------------------------------
-- RAG DOCUMENTS
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES rag_batches(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content_hash TEXT,
    chunk_count INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'chunked', 'embedded', 'failed')),
    error_message TEXT,
    doc_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_documents_batch ON rag_documents(batch_id);
CREATE INDEX IF NOT EXISTS idx_rag_documents_hash ON rag_documents(content_hash);

-- -----------------------------------------------------------
-- RAG CATEGORIES (knowledge domains for the agent)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    retrieval_config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(agent_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_rag_categories_agent ON rag_categories(agent_id);

-- Default categories per agent (inserted via application, examples):
-- slug: 'products'          → Contexto de productos/servicios
-- slug: 'company_history'   → Historia, logros, manejo de criticas
-- slug: 'forbidden_topics'  → Tematicas que el agente NO debe tocar
-- slug: 'qa_guidelines'     → Criterios de calidad para auto-evaluacion

-- -----------------------------------------------------------
-- RAG CHUNKS (embedded text fragments with pgvector)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
    category_id UUID REFERENCES rag_categories(id) ON DELETE SET NULL,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    embedding vector(384),
    chunk_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_document ON rag_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_category ON rag_chunks(category_id);

-- HNSW index for fast approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding
    ON rag_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- -----------------------------------------------------------
-- RAG FORBIDDEN TOPICS (explicit blocklist per agent)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_forbidden_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    description TEXT,
    severity TEXT NOT NULL DEFAULT 'block'
        CHECK (severity IN ('block', 'warn', 'redirect')),
    redirect_message TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_forbidden_agent ON rag_forbidden_topics(agent_id);

-- -----------------------------------------------------------
-- QA CRITERIA (scoring rubrics for call quality)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS qa_criteria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL DEFAULT 'general'
        CHECK (category IN ('greeting', 'resolution', 'empathy', 'compliance', 'closing', 'general')),
    max_score INTEGER NOT NULL DEFAULT 10,
    weight FLOAT NOT NULL DEFAULT 1.0,
    is_automated BOOLEAN NOT NULL DEFAULT FALSE,
    automation_config JSONB DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_qa_criteria_org ON qa_criteria(org_id);

-- -----------------------------------------------------------
-- QA EVALUATIONS (one evaluation per conversation)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS qa_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    evaluator_type TEXT NOT NULL DEFAULT 'auto'
        CHECK (evaluator_type IN ('auto', 'human', 'hybrid')),
    evaluator_id TEXT,
    overall_score FLOAT,
    max_possible_score FLOAT,
    percentage FLOAT,
    notes TEXT,
    evaluation_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_qa_evaluations_conversation ON qa_evaluations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_qa_evaluations_agent ON qa_evaluations(agent_id);
CREATE INDEX IF NOT EXISTS idx_qa_evaluations_created ON qa_evaluations(created_at);

-- -----------------------------------------------------------
-- QA SCORES (individual criterion scores per evaluation)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS qa_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID NOT NULL REFERENCES qa_evaluations(id) ON DELETE CASCADE,
    criterion_id UUID NOT NULL REFERENCES qa_criteria(id) ON DELETE CASCADE,
    score FLOAT NOT NULL DEFAULT 0,
    max_score FLOAT NOT NULL DEFAULT 10,
    notes TEXT,
    evidence TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(evaluation_id, criterion_id)
);

CREATE INDEX IF NOT EXISTS idx_qa_scores_evaluation ON qa_scores(evaluation_id);

-- -----------------------------------------------------------
-- PROCESS METADATA
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS process_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    stage TEXT NOT NULL
        CHECK (stage IN ('stt', 'llm', 'tts', 'denoise', 'rag', 'sentiment')),
    input_hash TEXT,
    output_hash TEXT,
    latency_ms INTEGER,
    model_used TEXT,
    parameters JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_process_metadata_conversation ON process_metadata(conversation_id);
CREATE INDEX IF NOT EXISTS idx_process_metadata_stage ON process_metadata(stage);
CREATE INDEX IF NOT EXISTS idx_process_metadata_created ON process_metadata(created_at);

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
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_agents_updated_at') THEN
        CREATE TRIGGER update_agents_updated_at
            BEFORE UPDATE ON agents
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_context_profiles_updated_at') THEN
        CREATE TRIGGER update_context_profiles_updated_at
            BEFORE UPDATE ON context_profiles
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_rag_batches_updated_at') THEN
        CREATE TRIGGER update_rag_batches_updated_at
            BEFORE UPDATE ON rag_batches
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_rag_categories_updated_at') THEN
        CREATE TRIGGER update_rag_categories_updated_at
            BEFORE UPDATE ON rag_categories
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_qa_evaluations_updated_at') THEN
        CREATE TRIGGER update_qa_evaluations_updated_at
            BEFORE UPDATE ON qa_evaluations
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END
$$;
