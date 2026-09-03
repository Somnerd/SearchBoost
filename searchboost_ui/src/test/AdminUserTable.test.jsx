import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AdminUserTable from '../components/AdminUserTable';

describe('AdminUserTable Component', () => {
  const mockUsers = [
    { id: 1, username: 'admin_boss', role: 'admin', created_at: '2026-01-15T10:00:00Z' },
    { id: 2, username: 'charlie_member', role: 'user', created_at: '2026-02-20T12:30:00Z' },
    { id: 3, username: 'dave_coadmin', role: 'admin', created_at: '2026-03-01T08:15:00Z' },
  ];

  const currentUser = { id: 1, username: 'admin_boss', role: 'admin' };

  it('renders loading skeleton when loading prop is true', () => {
    const { container } = render(
      <AdminUserTable 
        users={[]} 
        currentUser={currentUser} 
        onRoleChange={vi.fn()} 
        onDelete={vi.fn()} 
        loading={true} 
      />
    );

    expect(container.querySelector('.glass-card')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('renders user rows and protects current user from self-modification', () => {
    render(
      <AdminUserTable 
        users={mockUsers} 
        currentUser={currentUser} 
        onRoleChange={vi.fn()} 
        onDelete={vi.fn()} 
        loading={false} 
      />
    );

    // Current user row
    expect(screen.getByText(/admin_boss \(You\)/i)).toBeInTheDocument();
    expect(screen.getByText('System Admin')).toBeInTheDocument();

    // Other users rows
    expect(screen.getByText('charlie_member')).toBeInTheDocument();
    expect(screen.getByText('dave_coadmin')).toBeInTheDocument();
  });

  it('invokes onRoleChange when clicking promote or demote buttons', () => {
    const handleRoleChange = vi.fn();
    render(
      <AdminUserTable 
        users={mockUsers} 
        currentUser={currentUser} 
        onRoleChange={handleRoleChange} 
        onDelete={vi.fn()} 
        loading={false} 
      />
    );

    // Promote charlie (user -> admin)
    const promoteBtn = screen.getByText('Make Admin');
    fireEvent.click(promoteBtn);
    expect(handleRoleChange).toHaveBeenCalledWith(2, 'admin');

    // Demote dave (admin -> user)
    const demoteBtn = screen.getByText('Demote to User');
    fireEvent.click(demoteBtn);
    expect(handleRoleChange).toHaveBeenCalledWith(3, 'user');
  });

  it('requires two-step confirmation before executing user deletion', () => {
    const handleDelete = vi.fn();
    render(
      <AdminUserTable 
        users={mockUsers} 
        currentUser={currentUser} 
        onRoleChange={vi.fn()} 
        onDelete={handleDelete} 
        loading={false} 
      />
    );

    // First delete button for charlie
    const deleteButtons = screen.getAllByText('Delete');
    fireEvent.click(deleteButtons[0]);

    // Should now display Confirm and Cancel
    const confirmBtn = screen.getByText('Confirm');
    const cancelBtn = screen.getByText('Cancel');
    expect(confirmBtn).toBeInTheDocument();
    expect(cancelBtn).toBeInTheDocument();

    // Cancel test
    fireEvent.click(cancelBtn);
    expect(screen.queryByText('Confirm')).not.toBeInTheDocument();
    expect(handleDelete).not.toHaveBeenCalled();

    // Now click delete again and confirm
    const deleteButtonsAfterCancel = screen.getAllByText('Delete');
    fireEvent.click(deleteButtonsAfterCancel[0]);
    const confirmBtnAfter = screen.getByText('Confirm');
    fireEvent.click(confirmBtnAfter);

    expect(handleDelete).toHaveBeenCalledTimes(1);
    expect(handleDelete).toHaveBeenCalledWith(2);
  });
});
