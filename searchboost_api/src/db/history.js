const pool = require('./pool');

/**
 * Fetches the conversation history for a specific user and reconstructs 
 * the query-result pairs.
 */
async function getHistory(username) {
  const sessionId = `SB-SESSION-${username}`;
  
  try {
    // Fetch all turns for this session, ordered by time
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

module.exports = { getHistory };
