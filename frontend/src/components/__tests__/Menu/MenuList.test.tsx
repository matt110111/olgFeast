import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import MenuList from '../../Menu/MenuList';

// Mock the API service
jest.mock('../../../services/api', () => ({
  apiService: {
    getFoodGroups: jest.fn(),
  },
}));

describe('MenuList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    const { apiService } = require('../../../services/api');
    apiService.getFoodGroups.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(<MenuList />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument(); // Loading text
  });

  it('renders menu items correctly', async () => {
    const mockFoodGroups = [
      {
        group: 'Appetizers',
        items: [
          {
            id: 1,
            name: 'Buffalo Wings',
            value: 12.99,
            ticket: 1,
            description: 'Spicy buffalo wings',
            is_available: true,
            created_at: '2025-01-01T00:00:00',
          },
        ],
      },
      {
        group: 'Main Course',
        items: [
          {
            id: 2,
            name: 'Grilled Salmon',
            value: 24.99,
            ticket: 2,
            description: 'Fresh grilled salmon',
            is_available: true,
            created_at: '2025-01-01T00:00:00',
          },
        ],
      },
    ];

    const { apiService } = require('../../../services/api');
    apiService.getFoodGroups.mockResolvedValue({ data: mockFoodGroups });

    render(<MenuList />);

    await waitFor(() => {
      expect(screen.getByText('Our Menu')).toBeInTheDocument();
      expect(screen.getByText('Appetizers')).toBeInTheDocument();
      expect(screen.getByText('Main Course')).toBeInTheDocument();
      expect(screen.getByText('Buffalo Wings')).toBeInTheDocument();
      expect(screen.getByText('Grilled Salmon')).toBeInTheDocument();
    });
  });

  it('displays food item details correctly', async () => {
    const mockFoodGroups = [
      {
        group: 'Appetizers',
        items: [
          {
            id: 1,
            name: 'Buffalo Wings',
            value: 12.99,
            ticket: 1,
            description: 'Spicy buffalo wings',
            is_available: true,
            created_at: '2025-01-01T00:00:00',
          },
        ],
      },
    ];

    const { apiService } = require('../../../services/api');
    apiService.getFoodGroups.mockResolvedValue({ data: mockFoodGroups });

    render(<MenuList />);

    await waitFor(() => {
      expect(screen.getByText('$12.99')).toBeInTheDocument();
      expect(screen.getByText('1 ticket')).toBeInTheDocument();
      expect(screen.getByText('5 min')).toBeInTheDocument(); // ticket * 5
      expect(screen.getByText('Spicy buffalo wings')).toBeInTheDocument();
    });
  });

  it('displays error message on API failure', async () => {
    const { apiService } = require('../../../services/api');
    apiService.getFoodGroups.mockRejectedValue(new Error('API Error'));

    render(<MenuList />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load menu items')).toBeInTheDocument();
    });
  });

  it('handles empty menu gracefully', async () => {
    const { apiService } = require('../../../services/api');
    apiService.getFoodGroups.mockResolvedValue({ data: [] });

    render(<MenuList />);

    await waitFor(() => {
      expect(screen.getByText('Our Menu')).toBeInTheDocument();
      // Should not crash or show error
    });
  });

  it('renders add to cart buttons', async () => {
    const mockFoodGroups = [
      {
        group: 'Appetizers',
        items: [
          {
            id: 1,
            name: 'Buffalo Wings',
            value: 12.99,
            ticket: 1,
            description: 'Spicy buffalo wings',
            is_available: true,
            created_at: '2025-01-01T00:00:00',
          },
        ],
      },
    ];

    const { apiService } = require('../../../services/api');
    apiService.getFoodGroups.mockResolvedValue({ data: mockFoodGroups });

    render(<MenuList />);

    await waitFor(() => {
      const addButtons = screen.getAllByRole('button', { name: /add/i });
      expect(addButtons).toHaveLength(1);
    });
  });
});
