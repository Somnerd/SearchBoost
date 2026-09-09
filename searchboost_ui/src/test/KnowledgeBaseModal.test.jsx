import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import KnowledgeBaseModal from '../components/KnowledgeBaseModal';
import client from '../api/client';

describe('KnowledgeBaseModal Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when isOpen is false', () => {
    const { container } = render(<KnowledgeBaseModal isOpen={false} onClose={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });

  it('fetches and displays document sources and statistics on open', async () => {
    vi.spyOn(client, 'get').mockResolvedValueOnce({
      data: {
        totalChunks: 10,
        totalSources: 2,
        sources: ['docs/arch.md', 'docs/specs.md']
      }
    });

    render(<KnowledgeBaseModal isOpen={true} onClose={vi.fn()} />);

    expect(screen.getByText('Loading knowledge documents...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Knowledge Base Manager')).toBeInTheDocument();
      expect(screen.getByText('docs/arch.md')).toBeInTheDocument();
      expect(screen.getByText('docs/specs.md')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('⚡ HNSW + BM25 RRF')).toBeInTheDocument();
    });
  });

  it('handles empty state when no documents exist', async () => {
    vi.spyOn(client, 'get').mockResolvedValueOnce({
      data: {
        totalChunks: 0,
        totalSources: 0,
        sources: []
      }
    });

    render(<KnowledgeBaseModal isOpen={true} onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/No documents indexed yet/i)).toBeInTheDocument();
    });
  });

  it('deletes document source when delete button clicked', async () => {
    vi.spyOn(client, 'get')
      .mockResolvedValueOnce({
        data: {
          totalChunks: 5,
          totalSources: 1,
          sources: ['docs/old.md']
        }
      })
      .mockResolvedValueOnce({
        data: {
          totalChunks: 0,
          totalSources: 0,
          sources: []
        }
      });

    vi.spyOn(client, 'delete').mockResolvedValueOnce({
      data: { message: 'Deleted', sourceFile: 'docs/old.md', deletedChunks: 5 }
    });

    render(<KnowledgeBaseModal isOpen={true} onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('docs/old.md')).toBeInTheDocument();
    });

    const deleteBtn = screen.getByRole('button', { name: /Delete docs\/old\.md/i });
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(client.delete).toHaveBeenCalledWith('/search/docs', {
        params: { source: 'docs/old.md' }
      });
      expect(screen.getByText(/Deleted document source: docs\/old\.md/i)).toBeInTheDocument();
    });
  });

  it('submits raw document note and refreshes list', async () => {
    vi.spyOn(client, 'get')
      .mockResolvedValueOnce({
        data: { totalChunks: 0, totalSources: 0, sources: [] }
      })
      .mockResolvedValueOnce({
        data: { totalChunks: 2, totalSources: 1, sources: ['notes/release-notes.md'] }
      });

    vi.spyOn(client, 'post').mockResolvedValueOnce({
      data: {
        message: "Successfully indexed 2 chunks for 'notes/release-notes.md'",
        sourceFile: 'notes/release-notes.md',
        chunksIngested: 2
      }
    });

    render(<KnowledgeBaseModal isOpen={true} onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Document Title/i)).toBeInTheDocument();
    });

    const titleInput = screen.getByPlaceholderText(/Document Title/i);
    const contentTextarea = screen.getByPlaceholderText(/Paste Markdown notes/i);
    const submitBtn = screen.getByRole('button', { name: /Ingest Document/i });

    fireEvent.change(titleInput, { target: { value: 'release-notes' } });
    fireEvent.change(contentTextarea, { target: { value: 'v2.0 includes pgvector HNSW and hybrid RRF.' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(client.post).toHaveBeenCalledWith('/search/docs/raw', {
        title: 'release-notes',
        content: 'v2.0 includes pgvector HNSW and hybrid RRF.'
      });
      expect(screen.getByText(/Successfully indexed 2 chunks/i)).toBeInTheDocument();
    });
  });

  it('triggers sync when clicking Sync Files button', async () => {
    vi.spyOn(client, 'get').mockResolvedValueOnce({
      data: { totalChunks: 2, totalSources: 1, sources: ['docs/arch.md'] }
    });

    vi.spyOn(client, 'post').mockResolvedValueOnce({
      data: {
        status: 'synced',
        totalChunks: 8,
        totalSources: 3,
        sources: ['docs/arch.md', 'docs/guide.md', 'docs/api.md']
      }
    });

    render(<KnowledgeBaseModal isOpen={true} onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('docs/arch.md')).toBeInTheDocument();
    });

    const syncBtn = screen.getByRole('button', { name: /Sync Files/i });
    fireEvent.click(syncBtn);

    await waitFor(() => {
      expect(client.post).toHaveBeenCalledWith('/search/docs/sync');
      expect(screen.getByText(/Knowledge base synchronized successfully/i)).toBeInTheDocument();
      expect(screen.getByText('docs/guide.md')).toBeInTheDocument();
    });
  });
});
