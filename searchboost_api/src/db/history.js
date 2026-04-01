const pool = require('./pool');

/**
 * Fetches the conversation history for a specific user and reconstructs 
 * the query-result pairs.
 */
async function getSessions(username) {
  const escapedUsername = username.replace(/[\\%_]/g, '\\$&');
  const prefix = `SB-SESSION:${escapedUsername}:%`;
  try {
    const result = await pool.query(
      `SELECT t.id as thread_id, 
              COALESCE(MAX(c.created_at), t.created_at) as last_activity,
              t.title
       FROM threads t
       LEFT JOIN conversation_turns c ON c.session_id = 'SB-SESSION:' || $1 || ':' || t.id
       JOIN users u ON t.user_id = u.id
       WHERE u.username = $1
       GROUP BY t.id, t.created_at, t.title
       ORDER BY last_activity DESC`,
       [username]
    );

    return result.rows.map(r => ({
      thread_id: r.thread_id,
      session_id: `SB-SESSION:${username}:${r.thread_id}`,
      last_activity: r.last_activity,
      title: r.title
    }));
  } catch (err) {
    console.error('getSessions Error:', err);
    throw err;
  }
}

async function getHistory(sessionId) {
  try {
    const result = await pool.query(
      'SELECT role, content, created_at FROM conversation_turns WHERE session_id = $1 ORDER BY created_at ASC',
      [sessionId]
    );

    const turns = result.rows;
    const history = [];

    // Reconstruct pairs of { query, result }
    // We assume a 'user' turn is followed by an 'assistant' turn.
    for (let i = 0; i < turns.length; i++) {
      if (turns[i].role === 'user') {
        const query = turns[i].content;
        let answer = '...'; // Placeholder

        // Look for the next 'assistant' turn
        if (i + 1 < turns.length && turns[i+1].role === 'assistant') {
          answer = turns[i+1].content;
          i++; // Skip the assistant turn in the next loop iteration
        }

        history.push({
          query,
          result: answer
        });
      }
    }

    return history;
  } catch (err) {
    console.error('getHistory Error:', err);
    throw err;
  }
}

async function searchHistory(username, queryVector, limit = 5) {
  const escapedUsername = username.replace(/[\\%_]/g, '\\$&');
  const sessionPrefix = `SB-SESSION:${escapedUsername}:%`;
  try {
    const result = await pool.query(
      `SELECT session_id, role, content, created_at, 
              (embedding <=> $1) as distance
       FROM conversation_turns 
       WHERE session_id LIKE $2 ESCAPE '\\'
         AND embedding IS NOT NULL
       ORDER BY distance ASC
       LIMIT $3`,
      [queryVector, sessionPrefix, limit]
    );
    return result.rows;
  } catch (err) {
    console.error('searchHistory Error:', err);
    throw err;
  }
}

async function ensureThread(userId, threadId) {
  console.log(`[DB] ensureThread called for user=${userId}, thread=${threadId}`);
  try {
    const res = await pool.query(
      'INSERT INTO threads (id, user_id) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING',
      [threadId, userId]
    );
    console.log(`[DB] ensureThread result: rowsAffected=${res.rowCount}`);
  } catch (err) {
    console.error('[DB] ensureThread Error:', err);
    throw err;
  }
}

module.exports = { getHistory, getSessions, searchHistory, ensureThread };
