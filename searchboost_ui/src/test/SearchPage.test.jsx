import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import Search from '../pages/Search';
import client from '../api/client';
import * as AuthContext from '../context/AuthContext';

describe('Search Page Component', () => {
  const mockUser = { id: 5, username: 'operator', role: 'user' };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: mockUser,
      logout: vi.fn(),
    });

    let loadedInitialHistory = false;
    vi.spyOn(client, 'get').mockImplementation((url) => {
      if (url === '/search/sessions') {
        return Promise.resolve({
          data: [
            { thread_id: 'default', last_activity: '2026-09-03T10:00:00Z' },
            { thread_id: 'thread-9999', last_activity: '2026-09-03T11:00:00Z' },
          ],
        });
      }
      if (url.startsWith('/search/history/')) {
        if (!loadedInitialHistory) {
          loadedInitialHistory = true;
          return Promise.resolve({
            data: [
              { query: 'initial historical query', result: 'initial historical answer' },
            ],
          });
        }
        return Promise.resolve({ data: [] });
      }
      return Promise.reject(new Error('not found'));
    });
  });

  it('renders sidebar, model selector, search input, and historical turns on load', async () => {
    render(<Search />);

    expect(screen.getByText('+ New Thread')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Search history.../i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask anything.../i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Global Sandbox')).toBeInTheDocument();
      expect(screen.getByText('initial historical query')).toBeInTheDocument();
      expect(screen.getByText('initial historical answer')).toBeInTheDocument();
    });
  });

  it('changes selected LLM model from the dropdown', async () => {
    render(<Search />);

    await waitFor(() => {
      expect(screen.getByText('Global Sandbox')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    expect(select.value).toBe('llama3.2:latest');

    fireEvent.change(select, { target: { value: 'mistral:latest' } });
    expect(select.value).toBe('mistral:latest');
  });

  it('enqueues a research query and polls until completed', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    vi.spyOn(client, 'post').mockImplementation((url) => {
      if (url === '/search/enqueue') {
        return Promise.resolve({
          data: { id: 'SB-SESSION:operator:thread_1:uuid-123', status: 'queued' },
        });
      }
      return Promise.reject(new Error('not found'));
    });

    let pollCounter = 0;
    vi.spyOn(client, 'get').mockImplementation((url) => {
      if (url === '/search/sessions') return Promise.resolve({ data: [] });
      if (url.startsWith('/search/history/')) return Promise.resolve({ data: [] });
      if (url === '/search/result/SB-SESSION:operator:thread_1:uuid-123') {
        pollCounter++;
        if (pollCounter === 1) {
          return Promise.resolve({ data: { status: 'pending' } });
        }
        return Promise.resolve({
          data: {
            status: 'complete',
            result: { answer: 'Synthesized research answer from SearXNG + Ollama' },
          },
        });
      }
      return Promise.reject(new Error('not found'));
    });

    render(<Search />);

    const textarea = screen.getByPlaceholderText(/Ask anything.../i);
    const submitBtn = screen.getByTitle('Submit');

    fireEvent.change(textarea, { target: { value: 'What is vector search?' } });
    fireEvent.click(submitBtn);

    // Prompt added to conversation
    expect(screen.getByText('What is vector search?')).toBeInTheDocument();

    await waitFor(() => {
      expect(client.post).toHaveBeenCalledWith('/search/enqueue', expect.objectContaining({
        query: 'What is vector search?',
      }));
    });

    // Advance timer to trigger polling interval (2000ms)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2100);
    });

    // Advance timer again to complete polling
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2100);
    });

    await waitFor(() => {
      expect(screen.getByText('Synthesized research answer from SearXNG + Ollama')).toBeInTheDocument();
    });

    vi.useRealTimers();
  });

  it('performs semantic history search', async () => {
    vi.spyOn(client, 'post').mockImplementation((url) => {
      if (url === '/search/history/search') {
        return Promise.resolve({
          data: [
            { session_id: 'SB-SESSION:operator:thread-abc:uuid-1', content: 'historical match on rust memory' },
          ],
        });
      }
      return Promise.reject(new Error('not found'));
    });

    render(<Search />);

    await waitFor(() => {
      expect(screen.getByText('Global Sandbox')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search history.../i);
    fireEvent.change(searchInput, { target: { value: 'rust memory' } });
    fireEvent.submit(searchInput.closest('form'));

    await waitFor(() => {
      expect(screen.getByText(/Matches/i)).toBeInTheDocument();
      expect(screen.getByText(/historical match on rust memory/i)).toBeInTheDocument();
    });
  });

  it('resets conversation state when clicking + New Thread', async () => {
    render(<Search />);

    await waitFor(() => {
      expect(screen.getByText('initial historical query')).toBeInTheDocument();
    });

    const newThreadBtn = screen.getByText('+ New Thread');
    fireEvent.click(newThreadBtn);

    await waitFor(() => {
      expect(screen.queryByText('initial historical query')).not.toBeInTheDocument();
    });
  });
});
