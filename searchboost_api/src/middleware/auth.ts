import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

export interface UserPayload {
  id: number;
  username: string;
  role: string;
}

// Extend Express Request
declare module 'express-serve-static-core' {
  interface Request {
    user?: UserPayload;
  }
}

export function verifyToken(req: Request, res: Response, next: NextFunction): void {
  let token = req.cookies?.sb_token;

  // Fallback to Authorization: Bearer <token>
  if (!token && req.headers.authorization?.startsWith('Bearer ')) {
    token = req.headers.authorization.split(' ')[1];
  }

  if (!token) {
    res.status(401).json({ error: 'Authentication required' });
    return;
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET as string) as UserPayload;
    req.user = decoded; // { id, username, role }
    next();
  } catch (error: any) {
    if (error.name === 'TokenExpiredError') {
      res.status(401).json({ error: 'Session expired, please log in again' });
      return;
    }
    res.status(401).json({ error: 'Invalid token' });
    return;
  }
}

export function requireAdmin(req: Request, res: Response, next: NextFunction): void {
  if (!req.user || req.user.role !== 'admin') {
    res.status(403).json({ error: 'Admin access required' });
    return;
  }
  next();
}
