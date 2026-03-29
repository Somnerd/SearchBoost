const pool = require('./pool');

async function migrateDb() {
  const query = `
    CREATE EXTENSION IF NOT EXISTS vector;

    CREATE TABLE IF NOT EXISTS users (
      id          SERIAL PRIMARY KEY,
      username    VARCHAR(64) UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role        VARCHAR(16) NOT NULL DEFAULT 'user',
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS threads (
      id          VARCHAR(128) PRIMARY KEY,
      user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
      title       TEXT,
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    -- Support for semantic search via pgvector
    CREATE TABLE IF NOT EXISTS conversation_turns (
      id          SERIAL PRIMARY KEY,
      session_id  VARCHAR(255) NOT NULL,
      role        VARCHAR(16) NOT NULL, -- 'user', 'assistant'
      content     TEXT NOT NULL,
      embedding   VECTOR(768), -- Default size for nomic-embed-text/small models
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_turns_session_id ON conversation_turns(session_id);
    CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads(user_id);
    -- Vector index for fast semantic search (using HNSW)
    CREATE INDEX IF NOT EXISTS idx_turns_embedding ON conversation_turns USING hnsw (embedding vector_cosine_ops);
  `;
  try {
    await pool.query(query);
    console.log('Database migrated successfully (users, threads, turns checked/created).');
  } catch (error) {
    console.error('Error migrating database:', error);
    throw error;
  }
}

module.exports = migrateDb;
