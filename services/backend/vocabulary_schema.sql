-- Vocabulary Management Schema
-- Extension to the main database for voice corpus management

-- ===========================================
-- VOCABULARY CATEGORIES
-- ===========================================
CREATE TABLE IF NOT EXISTS vocabulary_categories (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id VARCHAR(36) REFERENCES vocabulary_categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default categories
INSERT INTO vocabulary_categories (id, name, description) VALUES
    ('cat-tech', 'Tecnología', 'Términos tecnológicos y redes sociales'),
    ('cat-brands', 'Marcas', 'Nombres de marcas y empresas'),
    ('cat-names', 'Nombres Propios', 'Nombres de personas y lugares'),
    ('cat-numbers', 'Números', 'Números y cantidades'),
    ('cat-greetings', 'Saludos', 'Saludos y despedidas'),
    ('cat-phrases', 'Frases Comunes', 'Frases de uso frecuente en call center')
ON CONFLICT (name) DO NOTHING;


-- ===========================================
-- VOCABULARY WORDS
-- ===========================================
CREATE TABLE IF NOT EXISTS vocabulary_words (
    id VARCHAR(36) PRIMARY KEY,
    word VARCHAR(255) NOT NULL,
    phonetic VARCHAR(255),  -- IPA pronunciation
    category_id VARCHAR(36) REFERENCES vocabulary_categories(id),
    audio_path VARCHAR(500),
    duration_seconds FLOAT,
    sample_count INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(word)
);

-- Create index for search
CREATE INDEX IF NOT EXISTS idx_vocabulary_words_word ON vocabulary_words(word);
CREATE INDEX IF NOT EXISTS idx_vocabulary_words_category ON vocabulary_words(category_id);


-- ===========================================
-- VOCABULARY PHRASES
-- ===========================================
CREATE TABLE IF NOT EXISTS vocabulary_phrases (
    id VARCHAR(36) PRIMARY KEY,
    phrase TEXT NOT NULL,
    category_id VARCHAR(36) REFERENCES vocabulary_categories(id),
    audio_path VARCHAR(500),
    duration_seconds FLOAT,
    context TEXT,  -- Usage context/scenario
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vocabulary_phrases_category ON vocabulary_phrases(category_id);


-- ===========================================
-- RECORDING GUIDES
-- ===========================================
CREATE TABLE IF NOT EXISTS recording_guides (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    items TEXT[] NOT NULL,  -- Array of words/phrases to record
    category_id VARCHAR(36) REFERENCES vocabulary_categories(id),
    estimated_duration_minutes FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ===========================================
-- PREDEFINED TECH VOCABULARY
-- ===========================================
INSERT INTO vocabulary_words (id, word, category_id, phonetic) VALUES
    -- Social Media & Tech
    (gen_random_uuid()::text, 'Facebook', 'cat-tech', 'ˈfeɪsbʊk'),
    (gen_random_uuid()::text, 'Instagram', 'cat-tech', 'ˈɪnstəɡræm'),
    (gen_random_uuid()::text, 'WhatsApp', 'cat-tech', 'ˈwɒtsæp'),
    (gen_random_uuid()::text, 'Twitter', 'cat-tech', 'ˈtwɪtər'),
    (gen_random_uuid()::text, 'TikTok', 'cat-tech', 'ˈtɪktɒk'),
    (gen_random_uuid()::text, 'YouTube', 'cat-tech', 'ˈjuːtuːb'),
    (gen_random_uuid()::text, 'LinkedIn', 'cat-tech', 'ˈlɪŋktɪn'),
    (gen_random_uuid()::text, 'Google', 'cat-tech', 'ˈɡuːɡəl'),
    (gen_random_uuid()::text, 'Microsoft', 'cat-tech', 'ˈmaɪkrəsɒft'),
    (gen_random_uuid()::text, 'Apple', 'cat-tech', 'ˈæpəl'),
    (gen_random_uuid()::text, 'Amazon', 'cat-tech', 'ˈæməzɒn'),
    (gen_random_uuid()::text, 'Netflix', 'cat-tech', 'ˈnetflɪks'),
    (gen_random_uuid()::text, 'Spotify', 'cat-tech', 'ˈspɒtɪfaɪ'),
    (gen_random_uuid()::text, 'Uber', 'cat-tech', 'ˈuːbər'),
    (gen_random_uuid()::text, 'WiFi', 'cat-tech', 'ˈwaɪfaɪ'),
    (gen_random_uuid()::text, 'Bluetooth', 'cat-tech', 'ˈbluːtuːθ'),
    (gen_random_uuid()::text, 'email', 'cat-tech', 'ˈiːmeɪl'),
    (gen_random_uuid()::text, 'software', 'cat-tech', 'ˈsɒftweər'),
    (gen_random_uuid()::text, 'hardware', 'cat-tech', 'ˈhɑːdweər'),
    (gen_random_uuid()::text, 'internet', 'cat-tech', 'ˈɪntərnet')
ON CONFLICT (word) DO NOTHING;

-- Call Center Phrases
INSERT INTO vocabulary_phrases (id, phrase, category_id, context) VALUES
    (gen_random_uuid()::text, 'Buenos días, gracias por llamar', 'cat-greetings', 'Saludo inicial'),
    (gen_random_uuid()::text, '¿En qué puedo ayudarle?', 'cat-greetings', 'Pregunta inicial'),
    (gen_random_uuid()::text, 'Un momento por favor', 'cat-phrases', 'Pausa'),
    (gen_random_uuid()::text, 'Permítame verificar', 'cat-phrases', 'Verificación'),
    (gen_random_uuid()::text, 'Gracias por su paciencia', 'cat-phrases', 'Espera'),
    (gen_random_uuid()::text, 'Su solicitud ha sido registrada', 'cat-phrases', 'Confirmación'),
    (gen_random_uuid()::text, '¿Hay algo más en lo que pueda ayudarle?', 'cat-phrases', 'Cierre'),
    (gen_random_uuid()::text, 'Que tenga un excelente día', 'cat-greetings', 'Despedida')
ON CONFLICT DO NOTHING;
