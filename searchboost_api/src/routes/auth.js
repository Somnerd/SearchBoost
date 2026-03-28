const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { findByUsername, createUser } = require('../db/users');
const { verifyToken } = require('../middleware/auth');

const router = express.Router();

router.post('/register', async (req, res, next) => {
  try {
    const { username, password } = req.body;
    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password are required' });
    }

    // Basic validation
    if (username.length < 3 || username.length > 32 || !/^[a-zA-Z0-9_]+$/.test(username)) {
      return res.status(400).json({ error: 'Username must be 3-32 alphanumeric characters or underscores' });
    }
    if (password.length < 8) {
      return res.status(400).json({ error: 'Password must be at least 8 characters long' });
    }

    const existingUser = await findByUsername(username);
    if (existingUser) {
      return res.status(409).json({ error: 'Username already taken' });
    }

    const passwordHash = await bcrypt.hash(password, 12);
    const newUser = await createUser(username, passwordHash);

    res.status(201).json(newUser);
  } catch (error) {
    next(error);
  }
});

router.post('/login', async (req, res, next) => {
  try {
    const { username, password } = req.body;
    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password are required' });
    }

    const user = await findByUsername(username);
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const match = await bcrypt.compare(password, user.password_hash);
    if (!match) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const payload = {
      id: user.id,
      username: user.username,
      role: user.role
    };

    const expiresInString = process.env.JWT_EXPIRES_IN || '24h';
    const matchTime = expiresInString.match(/^(\d+)([smhd])$/);
    let maxAge = 24 * 60 * 60 * 1000; // Default 24h
    if (matchTime) {
      const val = parseInt(matchTime[1]);
      const unit = matchTime[2];
      const multipliers = { s: 1000, m: 60 * 1000, h: 60 * 60 * 1000, d: 24 * 60 * 60 * 1000 };
      maxAge = val * multipliers[unit];
    }

    const token = jwt.sign(payload, process.env.JWT_SECRET, {
      expiresIn: expiresInString
    });

    res.cookie('sb_token', token, {
      httpOnly: true,
      sameSite: 'strict',
      secure: process.env.NODE_ENV === 'production',
      maxAge: maxAge
    });

    res.status(200).json(payload);
  } catch (error) {
    next(error);
  }
});

router.post('/logout', (req, res) => {
  res.clearCookie('sb_token');
  res.status(200).json({ message: 'Logged out' });
});

router.get('/me', verifyToken, (req, res) => {
  res.status(200).json(req.user);
});

module.exports = router;
