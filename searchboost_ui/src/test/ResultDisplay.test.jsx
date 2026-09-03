import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ResultDisplay from '../components/ResultDisplay';

describe('ResultDisplay Component', () => {
  it('returns null when result, loading, and error are absent', () => {
    const { container } = render(<ResultDisplay result={null} loading={false} error={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders loading thinking state with dot-pulse indicator', () => {
    render(<ResultDisplay result={null} loading={true} error={null} />);

    expect(screen.getByText('Thinking')).toBeInTheDocument();
  });

  it('renders error card with warning message when error is provided', () => {
    render(<ResultDisplay result={null} loading={false} error="Search failed: upstream engine timeout" />);

    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Search failed: upstream engine timeout')).toBeInTheDocument();
  });

  it('renders AI Response card with formatted text when result is provided', () => {
    const aiText = "Here are the results found:\n1. First item\n2. Second item";
    render(<ResultDisplay result={aiText} loading={false} error={null} />);

    expect(screen.getByText('AI Response')).toBeInTheDocument();
    expect(screen.getByText(/Here are the results found:/i)).toBeInTheDocument();
  });
});
