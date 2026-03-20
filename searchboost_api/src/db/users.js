const pool = require('./pool');

async function findByUsername(username) {
  const result = await pool.query('SELECT * FROM users WHERE username = $1', [username]);
  return result.rows[0] || null;
}

async function createUser(username, passwordHash) {
  const result = await pool.query(
    'INSERT INTO users (username, password_hash) VALUES ($1, $2) RETURNING id, username, role, created_at',
    [username, passwordHash]
  );
  return result.rows[0];
}

async function listUsers() {
  const result = await pool.query('SELECT id, username, role, created_at FROM users ORDER BY created_at DESC');
  return result.rows;
}

async function updateRole(id, role) {
  const result = await pool.query(
    'UPDATE users SET role = $1 WHERE id = $2 RETURNING id, username, role, created_at',
    [role, id]
  );
  return result.rows[0];
}

async function deleteUser(id) {
  await pool.query('DELETE FROM users WHERE id = $1', [id]);
}

module.exports = {
  findByUsername,
  createUser,
  listUsers,
  updateRole,
  deleteUser
};
