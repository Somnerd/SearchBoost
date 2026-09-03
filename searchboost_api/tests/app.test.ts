import request from 'supertest';
import jwt from 'jsonwebtoken';
import axios from 'axios';

process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test_jwt_secret_for_unit_tests_only';
process.env.DB_PASSWORD = 'mock_password';
process.env.WARDEN_URL = 'http://mock-warden:14141';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock prisma client
jest.mock('../src/db/prisma', () => ({
  prisma: {
    $queryRaw: jest.fn(),
    user: {
      findUnique: jest.fn(),
      create: jest.fn(),
      findMany: jest.fn(),
      update: jest.fn(),
      delete: jest.fn()
    },
    thread: {
      upsert: jest.fn(),
      findMany: jest.fn()
    }
  }
}));

import app from '../src/app';
import { prisma } from '../src/db/prisma';

const normalUserToken = jwt.sign(
  { id: 1, username: 'normal_user', role: 'user' },
  process.env.JWT_SECRET as string
);

const adminUserToken = jwt.sign(
  { id: 99, username: 'super_admin', role: 'admin' },
  process.env.JWT_SECRET as string
);

describe('API Integration & Route Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Health Check Endpoint (/health)', () => {
    it('GET /health should return 200 and healthy status when database is up', async () => {
      (prisma.$queryRaw as jest.Mock).mockResolvedValueOnce([{ 1: 1 }]);

      const res = await request(app).get('/health');
      expect(res.status).toBe(200);
      expect(res.body).toHaveProperty('status', 'healthy');
      expect(res.body).toHaveProperty('database', 'up');
      expect(res.body).toHaveProperty('timestamp');
    });

    it('GET /health should return 503 and unhealthy status when database is down', async () => {
      (prisma.$queryRaw as jest.Mock).mockRejectedValueOnce(new Error('DB connection refused'));

      const res = await request(app).get('/health');
      expect(res.status).toBe(503);
      expect(res.body).toHaveProperty('status', 'unhealthy');
      expect(res.body).toHaveProperty('database', 'down');
    });
  });

  describe('Authentication Routes (/api/auth)', () => {
    it('POST /api/auth/register should reject empty or invalid username/password', async () => {
      const res = await request(app)
        .post('/api/auth/register')
        .send({ username: 'ab', password: '123' });

      expect(res.status).toBe(400);
      expect(res.body).toHaveProperty('error');
    });

    it('POST /api/auth/login should reject missing credentials', async () => {
      const res = await request(app)
        .post('/api/auth/login')
        .send({});

      expect(res.status).toBe(400);
      expect(res.body).toHaveProperty('error');
    });

    it('GET /api/auth/me should reject unauthenticated requests', async () => {
      const res = await request(app).get('/api/auth/me');
      expect(res.status).toBe(401);
      expect(res.body).toHaveProperty('error', 'Authentication required');
    });

    it('GET /api/auth/me should return current user info when token is provided', async () => {
      (prisma.user.findUnique as jest.Mock).mockResolvedValueOnce({
        id: 1,
        username: 'normal_user',
        role: 'user',
        createdAt: new Date()
      });

      const res = await request(app)
        .get('/api/auth/me')
        .set('Authorization', `Bearer ${normalUserToken}`);

      expect(res.status).toBe(200);
      expect(res.body).toHaveProperty('username', 'normal_user');
      expect(res.body).toHaveProperty('role', 'user');
    });
  });

  describe('Admin Routes & RBAC Protection (/api/admin)', () => {
    it('GET /api/admin/users should reject unauthenticated requests with 401', async () => {
      const res = await request(app).get('/api/admin/users');
      expect(res.status).toBe(401);
      expect(res.body.error).toBe('Authentication required');
    });

    it('GET /api/admin/users should reject non-admin users with 403 Forbidden', async () => {
      const res = await request(app)
        .get('/api/admin/users')
        .set('Authorization', `Bearer ${normalUserToken}`);

      expect(res.status).toBe(403);
      expect(res.body.error).toBe('Admin access required');
    });

    it('GET /api/admin/users should allow admin users and return user list', async () => {
      (prisma.user.findMany as jest.Mock).mockResolvedValueOnce([
        { id: 1, username: 'normal_user', role: 'user', createdAt: new Date() },
        { id: 99, username: 'super_admin', role: 'admin', createdAt: new Date() }
      ]);

      const res = await request(app)
        .get('/api/admin/users')
        .set('Authorization', `Bearer ${adminUserToken}`);

      expect(res.status).toBe(200);
      expect(Array.isArray(res.body)).toBe(true);
      expect(res.body.length).toBe(2);
      expect(res.body[0].username).toBe('normal_user');
    });

    it('PATCH /api/admin/users/:id/role should prevent admin from modifying own role', async () => {
      const res = await request(app)
        .patch('/api/admin/users/99/role')
        .set('Authorization', `Bearer ${adminUserToken}`)
        .send({ role: 'user' });

      expect(res.status).toBe(400);
      expect(res.body.error).toBe('Cannot modify your own role');
    });

    it('PATCH /api/admin/users/:id/role should reject invalid role types', async () => {
      const res = await request(app)
        .patch('/api/admin/users/1/role')
        .set('Authorization', `Bearer ${adminUserToken}`)
        .send({ role: 'superoperator' });

      expect(res.status).toBe(400);
      expect(res.body.error).toBe('Role must be user or admin');
    });

    it('PATCH /api/admin/users/:id/role should successfully update other user role', async () => {
      (prisma.user.update as jest.Mock).mockResolvedValueOnce({
        id: 1,
        username: 'normal_user',
        role: 'admin',
        createdAt: new Date()
      });

      const res = await request(app)
        .patch('/api/admin/users/1/role')
        .set('Authorization', `Bearer ${adminUserToken}`)
        .send({ role: 'admin' });

      expect(res.status).toBe(200);
      expect(res.body.role).toBe('admin');
    });

    it('DELETE /api/admin/users/:id should prevent admin from deleting own account', async () => {
      const res = await request(app)
        .delete('/api/admin/users/99')
        .set('Authorization', `Bearer ${adminUserToken}`);

      expect(res.status).toBe(400);
      expect(res.body.error).toBe('Cannot delete your own account');
    });

    it('DELETE /api/admin/users/:id should allow admin to delete other users', async () => {
      (prisma.user.delete as jest.Mock).mockResolvedValueOnce({ id: 1 });

      const res = await request(app)
        .delete('/api/admin/users/1')
        .set('Authorization', `Bearer ${adminUserToken}`);

      expect(res.status).toBe(200);
      expect(res.body.message).toBe('User deleted');
    });

    it('GET /api/admin/health should return system status including Warden and database', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        status: 200,
        data: { status: 'healthy', circuit_breaker: 'closed' }
      });
      (prisma.$queryRaw as jest.Mock).mockResolvedValueOnce([{ 1: 1 }]);

      const res = await request(app)
        .get('/api/admin/health')
        .set('Authorization', `Bearer ${adminUserToken}`);

      expect(res.status).toBe(200);
      expect(res.body.warden.status).toBe('healthy');
      expect(res.body.database.status).toBe('healthy');
    });
  });

  describe('Search Routes & Distributed Relay (/api/search)', () => {
    it('POST /api/search/enqueue should reject unauthenticated requests with 401', async () => {
      const res = await request(app)
        .post('/api/search/enqueue')
        .send({ query: 'quantum computing research' });

      expect(res.status).toBe(401);
      expect(res.body.error).toBe('Authentication required');
    });

    it('POST /api/search/enqueue should reject missing query with 400', async () => {
      const res = await request(app)
        .post('/api/search/enqueue')
        .set('Authorization', `Bearer ${normalUserToken}`)
        .send({ options: {} });

      expect(res.status).toBe(400);
      expect(res.body.error).toBe('query is required');
    });

    it('POST /api/search/enqueue should forward payload conforming to Warden SearchRequest schema', async () => {
      (prisma.thread.upsert as jest.Mock).mockResolvedValueOnce({
        id: 'sess-001',
        userId: 1,
        title: 'New Conversation'
      });

      mockedAxios.post.mockResolvedValueOnce({
        status: 200,
        data: { status: 'queued', id: 'SB-SESSION:normal_user:sess-001:uuid-mock-1234' }
      });

      const res = await request(app)
        .post('/api/search/enqueue')
        .set('Authorization', `Bearer ${normalUserToken}`)
        .send({
          query: 'high-performance rust microservices',
          thread_id: 'sess-001',
          options: { engine: 'searxng' }
        });

      expect(res.status).toBe(200);
      expect(res.body.status).toBe('queued');
      expect(res.body.id).toBe('SB-SESSION:normal_user:sess-001:uuid-mock-1234');

      // Verify the proxied payload matches the Warden SearchRequest schema
      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://mock-warden:14141/enqueue',
        expect.objectContaining({
          query: 'high-performance rust microservices',
          thread_id: 'sess-001',
          username: 'normal_user',
          options: { engine: 'searxng' }
        }),
        expect.any(Object)
      );
    });

    it('POST /api/search/enqueue should return 503 when Warden gateway is offline', async () => {
      (prisma.thread.upsert as jest.Mock).mockResolvedValueOnce({
        id: 'default',
        userId: 1,
        title: 'New Conversation'
      });

      mockedAxios.post.mockRejectedValueOnce(new Error('Warden connection refused'));

      const res = await request(app)
        .post('/api/search/enqueue')
        .set('Authorization', `Bearer ${normalUserToken}`)
        .send({ query: 'test query' });

      expect(res.status).toBe(503);
      expect(res.body.error).toBe('Service Unavailable');
    });

    it('GET /api/search/result/:job_id should enforce IDOR protection against cross-user access', async () => {
      // Trying to fetch a job belonging to 'victim_user'
      const res = await request(app)
        .get('/api/search/result/SB-SESSION:victim_user:sess-1:uuid-1234')
        .set('Authorization', `Bearer ${normalUserToken}`);

      expect(res.status).toBe(403);
      expect(res.body.error).toBe('Unauthorized');
    });

    it('GET /api/search/result/:job_id should return completed result when user owns the job', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        status: 200,
        data: { status: 'complete', result: 'Search completed successfully.' }
      });

      const res = await request(app)
        .get('/api/search/result/SB-SESSION:normal_user:sess-001:uuid-mock-1234')
        .set('Authorization', `Bearer ${normalUserToken}`);

      expect(res.status).toBe(200);
      expect(res.body.status).toBe('complete');
      expect(res.body.result).toBe('Search completed successfully.');
      expect(mockedAxios.get).toHaveBeenCalledWith(
        'http://mock-warden:14141/results/SB-SESSION:normal_user:sess-001:uuid-mock-1234',
        expect.objectContaining({ params: { username: 'normal_user' } })
      );
    });

    it('GET /api/search/sessions should retrieve sessions mapped to thread_id for UI compatibility', async () => {
      (prisma.thread.findMany as jest.Mock).mockResolvedValueOnce([
        { id: 'sess-001', title: 'Conversation 1', createdAt: new Date() },
        { id: 'sess-002', title: 'Conversation 2', createdAt: new Date() }
      ]);

      const res = await request(app)
        .get('/api/search/sessions')
        .set('Authorization', `Bearer ${normalUserToken}`);

      expect(res.status).toBe(200);
      expect(Array.isArray(res.body)).toBe(true);
      expect(res.body[0].thread_id).toBe('sess-001');
      expect(res.body[1].thread_id).toBe('sess-002');
    });
  });
});
