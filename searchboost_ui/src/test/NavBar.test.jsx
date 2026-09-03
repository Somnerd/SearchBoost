import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import NavBar from '../components/NavBar';
import * as AuthContext from '../context/AuthContext';

describe('NavBar Component', () => {
  it('renders nothing when user is not authenticated', () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: null,
      logout: vi.fn(),
    });

    const { container } = render(
      <MemoryRouter>
        <NavBar />
      </MemoryRouter>
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders navigation links and username badge for standard user', () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: { id: 10, username: 'alice_researcher', role: 'user' },
      logout: vi.fn(),
    });

    render(
      <MemoryRouter>
        <NavBar />
      </MemoryRouter>
    );

    expect(screen.getByText('SearchBoost')).toBeInTheDocument();
    expect(screen.getByText('Search')).toBeInTheDocument();
    expect(screen.getByText('alice_researcher')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();

    // Standard user must not see Admin Panel
    expect(screen.queryByText('Admin Panel')).not.toBeInTheDocument();
    expect(screen.queryByText('Admin')).not.toBeInTheDocument();
  });

  it('renders Admin Panel link and Admin badge for admin user', () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: { id: 1, username: 'superadmin', role: 'admin' },
      logout: vi.fn(),
    });

    render(
      <MemoryRouter>
        <NavBar />
      </MemoryRouter>
    );

    expect(screen.getByText('SearchBoost')).toBeInTheDocument();
    expect(screen.getByText('Search')).toBeInTheDocument();
    expect(screen.getByText('Admin Panel')).toBeInTheDocument();
    expect(screen.getByText('superadmin')).toBeInTheDocument();
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('invokes logout handler when logout button is clicked', () => {
    const handleLogout = vi.fn();
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: { id: 2, username: 'bob', role: 'user' },
      logout: handleLogout,
    });

    render(
      <MemoryRouter>
        <NavBar />
      </MemoryRouter>
    );

    const logoutBtn = screen.getByText('Logout');
    fireEvent.click(logoutBtn);

    expect(handleLogout).toHaveBeenCalledTimes(1);
  });
});
