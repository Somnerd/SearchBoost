import express, { Request, Response, NextFunction } from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import ms from 'ms';
import { prisma } from '../db/prisma';
import { verifyToken } from '../middleware/auth';

// Fail-fast environment check
if (!process.env.JWT_SECRET) {
  throw new Error('FATAL: JWT_SECRET environment variable is not configured');
}

const router = express.Router();

router.post('/register', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { username, password } = req.body;
    if (typeof username !== 'string' || typeof password !== 'string') {
      res.status(400).json({ error: 'Username and password must be strings' });
      return;
    }
    if (!username || !password) {
      res.status(400).json({ error: 'Username and password are required' });
      return;
    }

    if (username.length < 3 || username.length > 32 || !/^[a-zA-Z0-9_]+$/.test(username)) {
      res.status(400).json({ error: 'Username must be 3-32 alphanumeric characters or underscores' });
      return;
    }
    if (password.length < 8) {
      res.status(400).json({ error: 'Password must be at least 8 characters long' });
      return;
    }

    const existingUser = await prisma.user.findUnique({ where: { username } });
    if (existingUser) {
      res.status(409).json({ error: 'Username already taken' });
      return;
    }

    const passwordHash = await bcrypt.hash(password, 12);
    const newUser = await prisma.user.create({
      data: {
        username,
        passwordHash
      },
      select: {
        id: true,
        username: true,
        role: true,
        createdAt: true
      }
    });

    res.status(201).json(newUser);
  } catch (error) {
    next(error);
  }
});

router.post('/login', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { username, password } = req.body;
    if (typeof username !== 'string' || typeof password !== 'string') {
      res.status(400).json({ error: 'Username and password must be strings' });
      return;
    }
    if (!username || !password) {
      res.status(400).json({ error: 'Username and password are required' });
      return;
    }

    const user = await prisma.user.findUnique({ where: { username } });
    if (!user) {
      res.status(401).json({ error: 'Invalid credentials' });
      return;
    }

    const match = await bcrypt.compare(password, user.passwordHash);
    if (!match) {
      res.status(401).json({ error: 'Invalid credentials' });
      return;
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

    const token = jwt.sign(payload, process.env.JWT_SECRET as string, {
      expiresIn: expiresInString as ms.StringValue
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

router.post('/logout', (req: Request, res: Response) => {
  res.clearCookie('sb_token', {
    httpOnly: true,
    sameSite: 'strict',
    secure: process.env.NODE_ENV === 'production'
  });
  res.status(200).json({ message: 'Logged out' });
});

router.get('/me', verifyToken, (req: Request, res: Response) => {
  res.status(200).json((req as any).user);
});

export default router;
