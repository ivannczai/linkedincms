// Remove unused React import
import { describe, test, expect, vi } from 'vitest'; // Remove unused beforeEach
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import StrategyView from './StrategyView';
import { Strategy } from '../../services/strategies';

// Mock strategy data
const mockStrategy: Strategy = {
  id: 1,
  client_id: 1,
  title: 'Test Strategy',
  details: '# Strategy Title\n\nThis is a **test** strategy with *markdown* content.',
  is_active: true,
  created_at: '2025-04-01T12:00:00Z',
  updated_at: '2025-04-02T12:00:00Z',
};

describe('StrategyView', () => {
  test('renders strategy title and date', () => {
    render(<StrategyView strategy={mockStrategy} />);
    
    expect(screen.getByText('Test Strategy')).toBeInTheDocument();
    expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
  });

  test('renders markdown content correctly', () => {
    render(<StrategyView strategy={mockStrategy} />);
    
    // Check that markdown is rendered as HTML
    const content = document.querySelector('.prose');
    expect(content).toBeInTheDocument();
    expect(content?.innerHTML).toContain('<h1>Strategy Title</h1>');
    expect(content?.innerHTML).toContain('<strong>test</strong>');
    expect(content?.innerHTML).toContain('<em>markdown</em>');
  });

  test('shows edit button for admin users', () => {
    const handleEdit = vi.fn();
    render(<StrategyView strategy={mockStrategy} onEdit={handleEdit} isAdmin={true} />);
    
    const editButton = screen.getByText('Edit Strategy');
    expect(editButton).toBeInTheDocument();
    
    // Test click handler
    userEvent.click(editButton);
    expect(handleEdit).toHaveBeenCalledTimes(1);
  });

  test('does not show edit button for non-admin users', () => {
    render(<StrategyView strategy={mockStrategy} isAdmin={false} />);
    
    expect(screen.queryByText('Edit Strategy')).not.toBeInTheDocument();
  });

  test('shows inactive warning when strategy is not active', () => {
    const inactiveStrategy = { ...mockStrategy, is_active: false };
    render(<StrategyView strategy={inactiveStrategy} />);
    
    expect(screen.getByText('This strategy is currently inactive.')).toBeInTheDocument();
  });

  test('does not show inactive warning when strategy is active', () => {
    render(<StrategyView strategy={mockStrategy} />);
    
    expect(screen.queryByText('This strategy is currently inactive.')).not.toBeInTheDocument();
  });
});
