vi.mock('../../../contexts/CartContext', () => ({ useCart: () => ({addToCart:vi.fn(),recentlyAdded:null,isLoading:false}) }));
import { apiService } from '../../../services/api';
import { vi } from 'vitest';
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import MenuList from '../../Menu/MenuList';

// Mock the API service
vi.mock('../../../services/api', () => ({
  apiService: {
    getFoodGroups: vi.fn(),
  },
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => ({
  ...await vi.importActual('react-router-dom'),
  useNavigate: () => vi.fn(),
}));

describe('MenuList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(apiService.getFoodGroups, { partial: true }).mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(<MenuList />);
    
    expect(screen.getByText('Loading menu...')).toBeInTheDocument(); // Loading text
  });

  it('renders menu items correctly', async () => {
    const mockFoodGroups = [
      {
        group: 'Appetizers',
        items: [
          {
            id: 1,
            food_group: "Dinner",
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
            food_group: "Dinner",
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

    vi.mocked(apiService.getFoodGroups, { partial: true }).mockResolvedValue({ data: mockFoodGroups });

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
            food_group: "Dinner",
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

    vi.mocked(apiService.getFoodGroups, { partial: true }).mockResolvedValue({ data: mockFoodGroups });

    render(<MenuList />);

    await waitFor(() => {
      expect(screen.getByText('1 tickets per portion')).toBeInTheDocument();
      expect(screen.getByText('1 ticket')).toBeInTheDocument();
      expect(screen.queryByText('5 min')).not.toBeInTheDocument();
      expect(screen.getByText('Spicy buffalo wings')).toBeInTheDocument();
    });
  });

  it('displays error message on API failure', async () => {
    vi.mocked(apiService.getFoodGroups, { partial: true }).mockRejectedValue(new Error('API Error'));

    render(<MenuList />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load menu items')).toBeInTheDocument();
    });
  });

  it('handles empty menu gracefully', async () => {
    vi.mocked(apiService.getFoodGroups, { partial: true }).mockResolvedValue({ data: [] });

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
            food_group: "Dinner",
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

    vi.mocked(apiService.getFoodGroups, { partial: true }).mockResolvedValue({ data: mockFoodGroups });

    render(<MenuList />);

    await waitFor(() => {
      const addButtons = screen.getAllByRole('button', { name: /add/i });
      expect(addButtons).toHaveLength(1);
    });
  });
});
