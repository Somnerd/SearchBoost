import express, { Request, Response, NextFunction } from 'express';
import axios from 'axios';
import { verifyToken } from '../middleware/auth';
import { prisma } from '../db/prisma';

const router = express.Router();

router.post('/enqueue', verifyToken, async (req: Request, res: Response, next: NextFunction) => {
  const { query, options, model } = req.body;
  if (!query) {
    res.status(400).json({ error: 'query is required' });
    return;
  }

  let thread_id = 'default';
  if (typeof req.body.thread_id === 'string' && /^[a-zA-Z0-9_-]+$/.test(req.body.thread_id)) {
    thread_id = req.body.thread_id;
  }

    // 🛡️ Security: Ensure thread exists in DB for Warden IDOR protection
    // This uses a composite unique constraint (userId, id) to prevent cross-user thread collisions.
    try {
        const userId = req.user!.id;
        await prisma.thread.upsert({
            where: { userId_id: { userId, id: thread_id } },
            update: {},
            create: { id: thread_id, userId: userId, title: 'New Conversation' }
        });
    } catch (err: any) {
        console.error(`[API] Thread Registration Failed: ${err.message}`);
        res.status(500).json({ error: 'Internal Server Error', details: 'Failed to initialize search session' });
        return;
    }

  const mergedOptions = { ...(options || {}), ...(model !== undefined ? { model } : {}) };

  const payload = {
    query,
    thread_id,
    username: req.user!.username,
    options: mergedOptions
  };

  console.log('[API] Proxying to Warden', {
    thread_id,
    model: mergedOptions.model,
    query_length: query.length
  });

  try {
    const response = await axios.post(`${process.env.WARDEN_URL}/enqueue`, payload, { 
      timeout: 5000,
      validateStatus: (status) => status < 300 // Force throw on non-2xx
    });
    res.status(response.status).json(response.data);
  } catch (error: any) {
    console.error(`[API] Warden Handshake Failed: ${error.message}`);
    // Mask raw Warden errors for security hardening
    res.status(503).json({ 
      error: 'Service Unavailable', 
      details: 'The search gateway is currently offline or unable to process this request.' 
    });
  }
});

router.get('/result/:job_id', verifyToken, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { job_id } = req.params;

    // job_id format: SB-SESSION:username:thread:uuid
    const parts = job_id.split(':');
    if (parts.length < 4 || parts[0] !== 'SB-SESSION' || parts[1] !== req.user!.username) {
      res.status(403).json({ error: 'Unauthorized' });
      return;
    }

    const response = await axios.get(`${process.env.WARDEN_URL}/results/${job_id}`, {
      params: { username: req.user!.username },
      timeout: 5000
    });
    res.status(response.status).json(response.data);
  } catch (error: any) {
    // Mask raw Warden errors for security hardening
    res.status(503).json({ error: 'Service Unavailable', details: 'The search proxy is currently unable to handle this request.' });
  }
});

router.get('/sessions', verifyToken, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const sessions = await prisma.thread.findMany({
      where: { user: { username: req.user!.username } },
      orderBy: { createdAt: 'desc' },
      select: { id: true, title: true, createdAt: true }
    });
    // Map 'id' to 'thread_id' to maintain compatibility with the React UI
    res.json(sessions.map(s => ({ ...s, thread_id: s.id })));
  } catch (err) {
    res.status(500).json({ error: 'Failed to retrieve sessions' });
  }
});

router.get(['/history', '/history/:thread_id'], verifyToken, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const threadParam = req.params.thread_id;
    let thread_id = 'default';
    if (typeof threadParam === 'string' && /^[a-zA-Z0-9_-]+$/.test(threadParam)) {
      thread_id = threadParam;
    }
    const session_id = `SB-SESSION:${req.user!.username}:${thread_id}`;
    
    const history = await prisma.conversationTurn.findMany({
      where: { sessionId: session_id },
      orderBy: { createdAt: 'asc' },
      select: {
          role: true,
          content: true,
          createdAt: true
      }
    });
    res.json(history);
  } catch (err) {
    res.status(500).json({ error: 'Failed to retrieve history' });
  }
});

router.post('/history/search', verifyToken, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { query, limit } = req.body;
    if (!query) {
      res.status(400).json({ error: 'query is required' });
      return;
    }

    // 1. Generate embedding using Ollama
    const ollamaUrl = process.env.OLLAMA_URL || 'http://sb_ollama:11434';
    const embedRes = await axios.post(`${ollamaUrl}/api/embeddings`, {
      model: 'nomic-embed-text',
      prompt: query
    }, { timeout: 5000 });
    const vector = embedRes.data.embedding;

    // 2. Search Database using raw query for pgvector operations
    // Using simple literal format suitable for Prisma
    const vectorLiteral = JSON.stringify(vector);
    const escapedUsername = req.user!.username
      .replace(/\\/g, '\\\\')
      .replace(/%/g, '\\%')
      .replace(/_/g, '\\_');
    const sessionLike = `SB-SESSION:${escapedUsername}:%`;
    
    // Safety fallback: if we can't search, return empty
    try {
        let safeLimit = parseInt(limit, 10);
        if (isNaN(safeLimit) || safeLimit < 1) safeLimit = 5;
        if (safeLimit > 100) safeLimit = 100;

        const results = await prisma.$queryRawUnsafe(`
          SELECT id, session_id, role, content, created_at as "createdAt"
          FROM conversation_turns
          WHERE session_id LIKE $1 ESCAPE '\\'
          ORDER BY embedding <=> $2::vector
          LIMIT $3
        `, sessionLike, vectorLiteral, safeLimit);
        
        res.json(results);
    } catch (e:any) {
        console.error("Vector search query failed (pgvector might be uninitialized):", e.message);
        res.json([]);
    }
  } catch (err: any) {
    console.error(`[API] Semantic History Search Failed: ${err.message}`);
    res.status(500).json({ error: 'Failed to retrieve relevant history' });
  }
});

export default router;
