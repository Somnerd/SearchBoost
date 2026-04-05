import dotenv from 'dotenv';
dotenv.config();

import express, { Request, Response, NextFunction } from 'express';
import cookieParser from 'cookie-parser';
import cors from 'cors';
import { prisma } from './db/prisma';

import authRoutes from './routes/auth';
import searchRoutes from './routes/search';
import adminRoutes from './routes/admin';

const app = express();

app.use(express.json());
app.use(cookieParser());
app.use(cors({
  origin: process.env.UI_ORIGIN || 'http://localhost:5173',
  credentials: true
}));

// Route mounting
app.use('/api/auth', authRoutes);
app.use('/api/search', searchRoutes);
app.use('/api/admin', adminRoutes);

app.get('/health', async (req: Request, res: Response) => {
  try {
    // Quick Prisma healthcheck
    await prisma.$queryRaw`SELECT 1`;
    res.status(200).json({ status: 'healthy', database: 'up', timestamp: new Date().toISOString() });
  } catch (err) {
    res.status(503).json({ status: 'unhealthy', database: 'down', timestamp: new Date().toISOString() });
  }
});

app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error('Unhandled error:', err);
  if (!res.headersSent) {
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

const PORT = process.env.PORT || 3001;

async function start() {
  const requiredEnv = ['JWT_SECRET', 'DB_PASSWORD'];
  const missing = requiredEnv.filter(k => !process.env[k]);
  
  if (missing.length > 0) {
    console.error(`FATAL: Missing mandatory environment variables: ${missing.join(', ')}`);
    process.exit(1);
  }
  
  try {
    // Note: Database migrations will be handled by Prisma CLI externally (e.g. `npx prisma db push`).
    app.listen(PORT, () => {
      console.log(`Node.js API server listening on port ${PORT}`);
    });
  } catch (error) {
    console.error('Startup failed:', error);
    process.exit(1);
  }
}

start();
