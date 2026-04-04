import express, { Request, Response, NextFunction } from 'express';
import axios from 'axios';
import { prisma } from '../db/prisma';
import { verifyToken, requireAdmin } from '../middleware/auth';

const router = express.Router();

router.use(verifyToken, requireAdmin);

router.get('/users', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const users = await prisma.user.findMany({
      select: {
        id: true,
        username: true,
        role: true,
        createdAt: true
      },
      orderBy: { createdAt: 'desc' }
    });
    res.status(200).json(users);
  } catch (error) {
    next(error);
  }
});

router.patch('/users/:id/role', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = parseInt(req.params.id, 10);
    const { role } = req.body;
    
    if (role !== 'user' && role !== 'admin') {
      res.status(400).json({ error: 'Role must be user or admin' });
      return;
    }
    
    if (req.user?.id === id) {
      res.status(400).json({ error: 'Cannot modify your own role' });
      return;
    }

    try {
      const updatedUser = await prisma.user.update({
        where: { id },
        data: { role },
        select: {
          id: true,
          username: true,
          role: true,
          createdAt: true
        }
      });
      res.status(200).json(updatedUser);
    } catch (e: any) {
      if (e.code === 'P2025') {
        res.status(404).json({ error: 'User not found' });
      } else {
        throw e;
      }
    }
  } catch (error) {
    next(error);
  }
});

router.delete('/users/:id', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = parseInt(req.params.id, 10);
    
    if (req.user?.id === id) {
      res.status(400).json({ error: 'Cannot delete your own account' });
      return;
    }

    try {
      await prisma.user.delete({ where: { id } });
      res.status(200).json({ message: 'User deleted' });
    } catch(e: any) {
      // Ignore if user isn't found
      res.status(200).json({ message: 'User deleted' });
    }
  } catch (error) {
    next(error);
  }
});

router.get('/health', async (req: Request, res: Response, next: NextFunction) => {
  let wardenStatus: any = { status: 'unreachable', circuit_breaker: 'unknown' };
  let databaseStatus: any = { status: 'unreachable' };

  try {
    const wardenHealth = await axios.get(`${process.env.WARDEN_URL}/health`, { timeout: 3000 });
    wardenStatus = wardenHealth.data;
  } catch (error) {
    // Keep it unreachable if it fails
  }

  try {
    await prisma.$queryRaw`SELECT 1`;
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

export default router;
