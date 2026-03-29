const express = require('express');
const axios = require('axios');
const { verifyToken } = require('../middleware/auth');
const { getHistory, getSessions } = require('../db/history');

const router = express.Router();

router.post('/enqueue', verifyToken, async (req, res, next) => {
  const { query, options } = req.body;
  if (!query) return res.status(400).json({ error: 'query is required' });

  let thread_id = 'default';
  if (typeof req.body.thread_id === 'string' && /^[a-zA-Z0-9_-]+$/.test(req.body.thread_id)) {
    thread_id = req.body.thread_id;
  }

  const payload = {
    query,
    thread_id,
    username: req.user.username,
    options: options || {}
  };

  console.log(`[API] Proxying to Warden: ${JSON.stringify(payload)}`);

  try {
    const response = await axios.post(`${process.env.WARDEN_URL}/enqueue`, payload, { 
      timeout: 5000,
      validateStatus: (status) => status < 300 // Force throw on non-2xx
    });
    res.status(response.status).json(response.data);
  } catch (error) {
    console.error(`[API] Warden Handshake Failed: ${error.message}`);
    // Mask raw Warden errors for security hardening
    res.status(503).json({ 
      error: 'Service Unavailable', 
      details: 'The search gateway is currently offline or unable to process this request.' 
    });
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
    // Mask raw Warden errors for security hardening
    res.status(503).json({ error: 'Service Unavailable', details: 'The search proxy is currently unable to handle this request.' });
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
    let thread_id = 'default';
    if (typeof threadParam === 'string' && /^[a-zA-Z0-9_-]+$/.test(threadParam)) {
      thread_id = threadParam;
    }
    const session_id = `SB-SESSION:${req.user.username}:${thread_id}`;
    
    const history = await getHistory(session_id);
    res.json(history);
  } catch (err) {
    res.status(500).json({ error: 'Failed to retrieve history' });
  }
});

module.exports = router;
