import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import Admin from '../pages/Admin';
import client from '../api/client';
import * as AuthContext from '../context/AuthContext';

describe('Admin Dashboard Page', () => {
  const adminUser = { id: 1, username: 'root_admin', role: 'admin' };
  const mockUsersList = [
    { id: 1, username: 'root_admin', role: 'admin', created_at: '2026-01-01T00:00:00Z' },
    { id: 2, username: 'developer_1', role: 'user', created_at: '2026-02-01T00:00:00Z' },
  ];
  const mockHealthData = {
    warden: { status: 'healthy', circuit_breaker: 'closed' },
    database: { status: 'healthy' },
    timestamp: '2026-09-03T11:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: adminUser,
      logout: vi.fn(),
    });
  });

  it('fetches users and health status concurrently on mount', async () => {
    vi.spyOn(client, 'get').mockImplementation((url) => {
      if (url === '/admin/users') return Promise.resolve({ data: mockUsersList });
      if (url === '/admin/health') return Promise.resolve({ data: mockHealthData });
      return Promise.reject(new Error('not found'));
    });

    render(<Admin />);

    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/root_admin \(You\)/i)).toBeInTheDocument();
      expect(screen.getByText('developer_1')).toBeInTheDocument();
      expect(screen.getByText('OK')).toBeInTheDocument();
      expect(screen.getByText('CONNECTED')).toBeInTheDocument();
    });
  });

  it('displays alert banner when administrative data fetch fails', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(client, 'get').mockRejectedValue(new Error('Network error'));

    render(<Admin />);

    expect(await screen.findByText('Failed to load administrative data. Some services may be unreachable.')).toBeInTheDocument();
    consoleSpy.mockRestore();
  });

  it('updates role via PATCH /admin/users/:id/role', async () => {
    vi.spyOn(client, 'get').mockImplementation((url) => {
      if (url === '/admin/users') return Promise.resolve({ data: mockUsersList });
      if (url === '/admin/health') return Promise.resolve({ data: mockHealthData });
      return Promise.reject(new Error('not found'));
    });
    vi.spyOn(client, 'patch').mockResolvedValueOnce({
      data: { id: 2, username: 'developer_1', role: 'admin' },
    });

    render(<Admin />);

    await waitFor(() => {
      expect(screen.getByText('developer_1')).toBeInTheDocument();
    });

    const makeAdminBtn = screen.getByText('Make Admin');
    fireEvent.click(makeAdminBtn);

    await waitFor(() => {
      expect(client.patch).toHaveBeenCalledWith('/admin/users/2/role', { role: 'admin' });
    });
  });

  it('deletes user via DELETE /admin/users/:id after confirmation', async () => {
    vi.spyOn(client, 'get').mockImplementation((url) => {
      if (url === '/admin/users') return Promise.resolve({ data: mockUsersList });
      if (url === '/admin/health') return Promise.resolve({ data: mockHealthData });
      return Promise.reject(new Error('not found'));
    });
    vi.spyOn(client, 'delete').mockResolvedValueOnce({
      data: { message: 'User deleted' },
    });

    render(<Admin />);

    await waitFor(() => {
      expect(screen.getByText('developer_1')).toBeInTheDocument();
    });

    // Step 1: Click delete
    const deleteBtn = screen.getByText('Delete');
    fireEvent.click(deleteBtn);

    // Step 2: Click confirm
    const confirmBtn = screen.getByText('Confirm');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(client.delete).toHaveBeenCalledWith('/admin/users/2');
      expect(screen.queryByText('developer_1')).not.toBeInTheDocument();
    });
  });
});
