const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const ms = require('ms');
const { findByUsername, createUser } = require('../db/users');
const { verifyToken } = require('../middleware/auth');

// Fail-fast environment check
if (!process.env.JWT_SECRET) {
  throw new Error('FATAL: JWT_SECRET environment variable is not configured');
}

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

    if (typeof username !== 'string' || typeof password !== 'string') {
      return res.status(400).json({ error: 'Invalid input types' });
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
    let maxAge = ms(expiresInString);

    if (maxAge === undefined) {
      const numericVal = parseInt(expiresInString, 10);
      maxAge = !isNaN(numericVal) ? numericVal * 1000 : 24 * 60 * 60 * 1000;
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
  res.clearCookie('sb_token', {
    httpOnly: true,
    sameSite: 'strict',
    secure: process.env.NODE_ENV === 'production'
  });
  res.status(200).json({ message: 'Logged out' });
});

router.get('/me', verifyToken, (req, res) => {
  res.status(200).json(req.user);
});

module.exports = router;
