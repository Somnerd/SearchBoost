import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute, AdminRoute } from '../components/ProtectedRoute';
import * as AuthContext from '../context/AuthContext';

describe('Route Protection Guards', () => {
  describe('ProtectedRoute', () => {
    it('shows loading state while authentication status is resolving', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        loading: true,
      });

      render(
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route element={<ProtectedRoute />}>
              <Route path="/protected" element={<div>Protected Content</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('redirects unauthenticated users to /login', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        loading: false,
      });

      render(
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route element={<ProtectedRoute />}>
              <Route path="/protected" element={<div>Protected Content</div>} />
            </Route>
            <Route path="/login" element={<div>Login Page</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Login Page')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('renders protected child component for authenticated user', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: { id: 1, username: 'authorized_user', role: 'user' },
        loading: false,
      });

      render(
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route element={<ProtectedRoute />}>
              <Route path="/protected" element={<div>Protected Content</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  describe('AdminRoute', () => {
    it('redirects unauthenticated users to /login', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        loading: false,
      });

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route element={<AdminRoute />}>
              <Route path="/admin" element={<div>Admin Panel</div>} />
            </Route>
            <Route path="/login" element={<div>Login Page</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Login Page')).toBeInTheDocument();
      expect(screen.queryByText('Admin Panel')).not.toBeInTheDocument();
    });

    it('redirects authenticated non-admin users to /search', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: { id: 2, username: 'regular_joe', role: 'user' },
        loading: false,
      });

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route element={<AdminRoute />}>
              <Route path="/admin" element={<div>Admin Panel</div>} />
            </Route>
            <Route path="/search" element={<div>Search Page</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Search Page')).toBeInTheDocument();
      expect(screen.queryByText('Admin Panel')).not.toBeInTheDocument();
    });

    it('renders admin component for admin user', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: { id: 1, username: 'sysadmin', role: 'admin' },
        loading: false,
      });

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route element={<AdminRoute />}>
              <Route path="/admin" element={<div>Admin Panel</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Admin Panel')).toBeInTheDocument();
    });
  });
});
