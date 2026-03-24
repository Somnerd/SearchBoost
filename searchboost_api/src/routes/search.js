const express = require('express');
const axios = require('axios');
const { verifyToken } = require('../middleware/auth');
const { getHistory } = require('../db/history');

const router = express.Router();

router.post('/enqueue', verifyToken, async (req, res, next) => {
  try {
    const { query, options } = req.body;
    if (!query) return res.status(400).json({ error: 'query is required' });

    const session_id = `SB-SESSION-${req.user.username}`;

    const response = await axios.post(`${process.env.WARDEN_URL}/enqueue`, {
      query,
      session_id,
      options: options || {}
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

router.get('/result/:job_id', verifyToken, async (req, res, next) => {
  try {
    const { job_id } = req.params;
    const response = await axios.get(`${process.env.WARDEN_URL}/results/${job_id}`);
    res.status(response.status).json(response.data);
  } catch (error) {
    if (error.response) {
      res.status(error.response.status).json(error.response.data);
    } else {
      res.status(503).json({ error: 'Could not reach Warden', details: error.message });
    }
  }
});

router.get('/history', verifyToken, async (req, res, next) => {
  try {
    const history = await getHistory(req.user.username);
    res.json(history);
  } catch (err) {
    res.status(500).json({ error: 'Failed to retrieve history' });
  }
});

module.exports = router;
