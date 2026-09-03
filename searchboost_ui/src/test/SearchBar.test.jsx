import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SearchBar from '../components/SearchBar';

describe('SearchBar Component', () => {
  it('renders textarea with placeholder and submit button', () => {
    render(<SearchBar onSubmit={vi.fn()} loading={false} />);
    
    const textarea = screen.getByPlaceholderText(/Ask anything... \(Ctrl\+Enter to submit\)/i);
    expect(textarea).toBeInTheDocument();
    expect(textarea).not.toBeDisabled();

    const submitBtn = screen.getByTitle('Submit');
    expect(submitBtn).toBeInTheDocument();
    expect(submitBtn).not.toBeDisabled();
  });

  it('calls onSubmit with trimmed query and resets textarea on button click', () => {
    const handleSubmit = vi.fn();
    render(<SearchBar onSubmit={handleSubmit} loading={false} />);

    const textarea = screen.getByPlaceholderText(/Ask anything.../i);
    const submitBtn = screen.getByTitle('Submit');

    fireEvent.change(textarea, { target: { value: '  how does vector search work?  ' } });
    fireEvent.click(submitBtn);

    expect(handleSubmit).toHaveBeenCalledTimes(1);
    expect(handleSubmit).toHaveBeenCalledWith('how does vector search work?');
    expect(textarea.value).toBe('');
  });

  it('submits on Ctrl+Enter keyboard shortcut', () => {
    const handleSubmit = vi.fn();
    render(<SearchBar onSubmit={handleSubmit} loading={false} />);

    const textarea = screen.getByPlaceholderText(/Ask anything.../i);

    fireEvent.change(textarea, { target: { value: 'Search query via shortcut' } });
    fireEvent.keyDown(textarea, { key: 'Enter', ctrlKey: true });

    expect(handleSubmit).toHaveBeenCalledTimes(1);
    expect(handleSubmit).toHaveBeenCalledWith('Search query via shortcut');
    expect(textarea.value).toBe('');
  });

  it('submits on Meta+Enter (Cmd+Enter on macOS)', () => {
    const handleSubmit = vi.fn();
    render(<SearchBar onSubmit={handleSubmit} loading={false} />);

    const textarea = screen.getByPlaceholderText(/Ask anything.../i);

    fireEvent.change(textarea, { target: { value: 'Mac shortcut query' } });
    fireEvent.keyDown(textarea, { key: 'Enter', metaKey: true });

    expect(handleSubmit).toHaveBeenCalledTimes(1);
    expect(handleSubmit).toHaveBeenCalledWith('Mac shortcut query');
  });

  it('does not submit when input is empty or whitespace only', () => {
    const handleSubmit = vi.fn();
    render(<SearchBar onSubmit={handleSubmit} loading={false} />);

    const textarea = screen.getByPlaceholderText(/Ask anything.../i);
    const submitBtn = screen.getByTitle('Submit');

    fireEvent.change(textarea, { target: { value: '    ' } });
    fireEvent.click(submitBtn);

    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it('disables textarea and button and displays spinner when loading', () => {
    const handleSubmit = vi.fn();
    render(<SearchBar onSubmit={handleSubmit} loading={true} />);

    const textarea = screen.getByPlaceholderText(/Ask anything.../i);
    const submitBtn = screen.getByTitle('Submit');

    expect(textarea).toBeDisabled();
    expect(submitBtn).toBeDisabled();

    // Trying to click submit should not invoke callback
    fireEvent.click(submitBtn);
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it('dynamically adjusts height on input event', () => {
    render(<SearchBar onSubmit={vi.fn()} loading={false} />);

    const textarea = screen.getByPlaceholderText(/Ask anything.../i);
    fireEvent.input(textarea, { target: { value: 'line 1\nline 2\nline 3' } });

    expect(textarea).toBeInTheDocument();
  });
});
