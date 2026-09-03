import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Login from '../pages/Login';
import Register from '../pages/Register';
import client from '../api/client';
import * as AuthContext from '../context/AuthContext';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Authentication Pages', () => {
  const mockLogin = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: null,
      login: mockLogin,
      logout: vi.fn(),
    });
  });

  describe('Login Page', () => {
    it('renders input fields, submit button, and registration link', () => {
      render(
        <MemoryRouter>
          <Login />
        </MemoryRouter>
      );

      expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
      expect(screen.getByText(/Don't have an account\?/i)).toBeInTheDocument();
    });

    it('displays validation error if required fields are omitted', async () => {
      render(
        <MemoryRouter>
          <Login />
        </MemoryRouter>
      );

      const submitBtn = screen.getByRole('button', { name: /Sign In/i });
      fireEvent.click(submitBtn);

      expect(await screen.findByText('Username and password are required')).toBeInTheDocument();
    });

    it('successfully logs in user and navigates to /search', async () => {
      vi.spyOn(client, 'post').mockResolvedValueOnce({
        data: { id: 10, username: 'charlie', role: 'user' },
      });

      render(
        <MemoryRouter>
          <Login />
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'charlie' } });
      fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'securepassword123' } });
      fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

      await waitFor(() => {
        expect(client.post).toHaveBeenCalledWith('/auth/login', {
          username: 'charlie',
          password: 'securepassword123',
        });
        expect(mockLogin).toHaveBeenCalledWith({ id: 10, username: 'charlie', role: 'user' });
        expect(mockNavigate).toHaveBeenCalledWith('/search');
      });
    });

    it('displays error message on invalid credentials (401)', async () => {
      vi.spyOn(client, 'post').mockRejectedValueOnce({
        response: { status: 401, data: { error: 'Invalid credentials' } },
      });

      render(
        <MemoryRouter>
          <Login />
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'baduser' } });
      fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'wrongpass' } });
      fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

      expect(await screen.findByText('Invalid username or password')).toBeInTheDocument();
    });
  });

  describe('Register Page', () => {
    it('enforces password confirmation equality', async () => {
      render(
        <MemoryRouter>
          <Register />
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/^Username/i), { target: { value: 'newoperator' } });
      fireEvent.change(screen.getByLabelText(/^Password/i), { target: { value: 'password1234' } });
      fireEvent.change(screen.getByLabelText(/Confirm Password/i), { target: { value: 'mismatchpass' } });
      fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));

      expect(await screen.findByText('Passwords do not match')).toBeInTheDocument();
    });

    it('enforces username format and length constraints', async () => {
      render(
        <MemoryRouter>
          <Register />
        </MemoryRouter>
      );

      // Too short username
      fireEvent.change(screen.getByLabelText(/^Username/i), { target: { value: 'ab' } });
      fireEvent.change(screen.getByLabelText(/^Password/i), { target: { value: 'password1234' } });
      fireEvent.change(screen.getByLabelText(/Confirm Password/i), { target: { value: 'password1234' } });
      fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));

      expect(await screen.findByText('Username must be 3-32 alphanumeric characters or underscores')).toBeInTheDocument();
    });

    it('successfully registers and auto-logs in user', async () => {
      vi.spyOn(client, 'post')
        .mockResolvedValueOnce({ data: { message: 'User created' } }) // register
        .mockResolvedValueOnce({ data: { id: 12, username: 'valid_user', role: 'user' } }); // login

      render(
        <MemoryRouter>
          <Register />
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/^Username/i), { target: { value: 'valid_user' } });
      fireEvent.change(screen.getByLabelText(/^Password/i), { target: { value: 'password1234' } });
      fireEvent.change(screen.getByLabelText(/Confirm Password/i), { target: { value: 'password1234' } });
      fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));

      await waitFor(() => {
        expect(client.post).toHaveBeenCalledTimes(2);
        expect(mockLogin).toHaveBeenCalledWith({ id: 12, username: 'valid_user', role: 'user' });
        expect(mockNavigate).toHaveBeenCalledWith('/search');
      });
    });

    it('handles username conflict (409)', async () => {
      vi.spyOn(client, 'post').mockRejectedValueOnce({
        response: { status: 409, data: { error: 'Username already taken' } },
      });

      render(
        <MemoryRouter>
          <Register />
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/^Username/i), { target: { value: 'existing_user' } });
      fireEvent.change(screen.getByLabelText(/^Password/i), { target: { value: 'password1234' } });
      fireEvent.change(screen.getByLabelText(/Confirm Password/i), { target: { value: 'password1234' } });
      fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));

      expect(await screen.findByText('Username already taken')).toBeInTheDocument();
    });
  });
});
