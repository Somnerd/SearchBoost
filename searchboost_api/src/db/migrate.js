const pool = require('./pool');

async function migrateDb() {
  const query = `
    CREATE TABLE IF NOT EXISTS users (
      id          SERIAL PRIMARY KEY,
      username    VARCHAR(64) UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role        VARCHAR(16) NOT NULL DEFAULT 'user',
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `;
  try {
    await pool.query(query);
    console.log('Database migrated successfully (users table checked/created).');
  } catch (error) {
    console.error('Error migrating database:', error);
    throw error;
  }
}

module.exports = migrateDb;
