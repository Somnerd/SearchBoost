const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  user: process.env.DB_USER || 'searchboost',
  password: process.env.DB_PASSWORD || 'searchboost_pass',
  database: process.env.DB_NAME || 'searchboost_db',
});

module.exports = pool;
