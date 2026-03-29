const express = require('express');
const axios = require('axios');
const pool = require('../db/pool');
const { listUsers, updateRole, deleteUser } = require('../db/users');
const { verifyToken, requireAdmin } = require('../middleware/auth');

const router = express.Router();

router.use(verifyToken, requireAdmin);

router.get('/users', async (req, res, next) => {
  try {
    const users = await listUsers();
    res.status(200).json(users);
  } catch (error) {
    next(error);
  }
});

router.patch('/users/:id/role', async (req, res, next) => {
  try {
    const { id } = req.params;
    const { role } = req.body;
    
    if (role !== 'user' && role !== 'admin') {
      return res.status(400).json({ error: 'Role must be user or admin' });
    }
    
    if (req.user.id === parseInt(id)) {
      return res.status(400).json({ error: 'Cannot modify your own role' });
    }

    const updatedUser = await updateRole(id, role);
    if (!updatedUser) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.status(200).json(updatedUser);
  } catch (error) {
    next(error);
  }
});

router.delete('/users/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    
    if (req.user.id === parseInt(id)) {
      return res.status(400).json({ error: 'Cannot delete your own account' });
    }

    await deleteUser(id);
    res.status(200).json({ message: 'User deleted' });
  } catch (error) {
    next(error);
  }
});

router.get('/health', async (req, res, next) => {
  let wardenStatus = { status: 'unreachable', circuit_breaker: 'unknown' };
  let databaseStatus = { status: 'unreachable' };

  try {
    const wardenHealth = await axios.get(`${process.env.WARDEN_URL}/health`, { timeout: 3000 });
    wardenStatus = wardenHealth.data;
  } catch (error) {
    // Keep it unreachable if it fails
  }

  try {
    await pool.query('SELECT 1');
    databaseStatus = { status: 'healthy' };
  } catch (error) {
    // Keep it unreachable
  }

  res.status(200).json({
    warden: wardenStatus,
    database: databaseStatus,
    timestamp: new Date().toISOString()
  });
});

module.exports = router;
