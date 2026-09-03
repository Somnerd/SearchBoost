import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import SystemHealth from '../components/SystemHealth';

describe('SystemHealth Component', () => {
  it('renders loading fallback cards when loading or health is null', () => {
    render(<SystemHealth health={null} loading={true} />);

    expect(screen.getByText('Warden Service')).toBeInTheDocument();
    expect(screen.getByText('Database (sb_db)')).toBeInTheDocument();
    // Default placeholder is ellipsis
    expect(screen.getAllByText('...').length).toBeGreaterThan(0);
  });

  it('renders healthy status indicators when services are fully operational', () => {
    const healthData = {
      warden: { status: 'healthy', circuit_breaker: 'closed' },
      database: { status: 'healthy' },
      timestamp: '2026-09-03T11:00:00.000Z',
    };

    render(<SystemHealth health={healthData} loading={false} />);

    expect(screen.getByText('OK')).toBeInTheDocument();
    expect(screen.getByText('CONNECTED')).toBeInTheDocument();
    expect(screen.getByText('Circuit: closed')).toBeInTheDocument();
    expect(screen.getByText('Pool active')).toBeInTheDocument();
    expect(screen.getByText(/Last Checked:/i)).toBeInTheDocument();
  });

  it('renders DOWN indicators when warden or database are degraded or unreachable', () => {
    const degradedData = {
      warden: { status: 'unreachable', circuit_breaker: 'tripped' },
      database: { status: 'unreachable' },
      timestamp: '2026-09-03T11:05:00.000Z',
    };

    render(<SystemHealth health={degradedData} loading={false} />);

    const downStatuses = screen.getAllByText('DOWN');
    expect(downStatuses.length).toBe(2);
    expect(screen.getByText('Circuit: tripped')).toBeInTheDocument();
    expect(screen.getByText('Check logs')).toBeInTheDocument();
  });
});
