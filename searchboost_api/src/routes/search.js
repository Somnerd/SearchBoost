const express = require('express');
const axios = require('axios');
const { verifyToken } = require('../middleware/auth');
const { getHistory, getSessions } = require('../db/history');

const router = express.Router();

router.post('/enqueue', verifyToken, async (req, res, next) => {
  try {
    const { query, options } = req.body;
    if (!query) return res.status(400).json({ error: 'query is required' });

    const thread_id = req.body.thread_id && req.body.thread_id !== 'default' ? req.body.thread_id : 'default';

    const response = await axios.post(`${process.env.WARDEN_URL}/enqueue`, {
      query,
      thread_id: thread_id,
      username: req.user.username,
      options: options || {}
    }, { timeout: 5000 });

    res.status(response.status).json(response.data);
  } catch (error) {
    if (error.response) {
      res.status(error.response.status).json(error.response.data);
    } else {
      res.status(503).json({ error: 'Could not reach Warden', details: error.message });
    }
  }
});

router.get('/result/:job_id', verifyToken, async (req, res, next) => {
  try {
    const { job_id } = req.params;

    // job_id format: SB-SESSION:username:thread:uuid
    const parts = job_id.split(':');
    if (parts.length < 4 || parts[0] !== 'SB-SESSION' || parts[1] !== req.user.username) {
      return res.status(403).json({ error: 'Unauthorized' });
    }

    const response = await axios.get(`${process.env.WARDEN_URL}/results/${job_id}`, {
      params: { username: req.user.username },
      timeout: 5000
    });
    res.status(response.status).json(response.data);
  } catch (error) {
    if (error.response) {
      res.status(error.response.status).json(error.response.data);
    } else {
      res.status(503).json({ error: 'Could not reach Warden', details: error.message });
    }
  }
});

router.get('/sessions', verifyToken, async (req, res, next) => {
  try {
    const sessions = await getSessions(req.user.username);
    res.json(sessions);
  } catch (err) {
    res.status(500).json({ error: 'Failed to retrieve sessions' });
  }
});

router.get(['/history', '/history/:thread_id'], verifyToken, async (req, res, next) => {
  try {
    const threadParam = req.params.thread_id;
    const thread_id = threadParam && threadParam !== 'default' ? threadParam : 'default';
    const session_id = `SB-SESSION:${req.user.username}:${thread_id}`;
    
    const history = await getHistory(session_id);
    res.json(history);
  } catch (err) {
    res.status(500).json({ error: 'Failed to retrieve history' });
  }
});

module.exports = router;
