-- Enable the pgvector extension to store and search vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Create User Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Create Question Table
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    topic_tag VARCHAR(100),
    embedding vector(384), -- Dimension 384 matches sentence-transformers like 'all-MiniLM-L6-v2'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Search History Table (History)
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    similar_questions INTEGER[] -- Array storing IDs of similar questions found
);

-- Create an HNSW index on the questions embedding for fast similarity searches
-- Note: Adjust the operator if using L2 distance (vector_l2_ops) or inner product (vector_ip_ops)
CREATE INDEX IF NOT EXISTS questions_embedding_cosine_idx 
ON questions USING hnsw (embedding vector_cosine_ops);
