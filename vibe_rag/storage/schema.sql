-- PostgreSQL + pgvector schema for vibe-rag vector storage
-- This schema creates tables for storing documents with vector embeddings

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Example table creation (replace 'documents' with your collection name)
-- This is a template - actual tables are created dynamically by PostgresVectorStore

-- CREATE TABLE IF NOT EXISTS documents (
--     id TEXT PRIMARY KEY,
--     content TEXT NOT NULL,
--     metadata JSONB DEFAULT '{}',
--     embedding vector(768)  -- Dimension can be configured
-- );

-- Example index for similarity search using cosine distance
-- CREATE INDEX IF NOT EXISTS documents_embedding_idx
-- ON documents
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- Note: The actual table and index creation is handled by PostgresVectorStore.initialize()
-- This schema file is provided as a reference for manual setup or migrations.

-- For production use, consider:
-- 1. Adjusting the vector dimension based on your embedding model
-- 2. Tuning the IVFFlat lists parameter (rule of thumb: sqrt(num_rows))
-- 3. Adding indexes on frequently filtered metadata fields
-- 4. Setting up appropriate database roles and permissions

-- Example metadata index for filtering by source:
-- CREATE INDEX IF NOT EXISTS documents_metadata_source_idx
-- ON documents ((metadata->>'source'));
