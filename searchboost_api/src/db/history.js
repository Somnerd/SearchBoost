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
      `SELECT session_id, MAX(created_at) as last_activity
       FROM conversation_turns
       WHERE session_id LIKE $1 ESCAPE '\\'
       GROUP BY session_id
       ORDER BY last_activity DESC`, 
       [prefix]
    );

    return result.rows.map(r => {
      // session_id: SB-SESSION:username:thread_id
      const parts = r.session_id.split(':');
      const threadId = parts[2] || 'default';
      return {
        thread_id: threadId,
        session_id: r.session_id,
        last_activity: r.last_activity
      };
    });
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

module.exports = { getHistory, getSessions };
