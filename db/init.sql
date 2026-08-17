-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table for visa information chunks
CREATE TABLE IF NOT EXISTS visa_chunks (
    id SERIAL PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    topic VARCHAR(200) NOT NULL,
    chunk_text TEXT NOT NULL,
    source_url TEXT,
    metadata JSONB DEFAULT '{}',
    embedding vector(384),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast similarity search (rebuild when table has enough rows)
-- CREATE INDEX IF NOT EXISTS idx_visa_chunks_embedding
--     ON visa_chunks USING ivfflat (embedding vector_cosine_ops)
--     WITH (lists = 10);

-- Index for country filtering
CREATE INDEX IF NOT EXISTS idx_visa_chunks_country
    ON visa_chunks (country);

-- View for checking scrape status
CREATE OR REPLACE VIEW scrape_status AS
SELECT country, COUNT(*) as chunk_count, MAX(created_at) as last_scraped
FROM visa_chunks
GROUP BY country;
