import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../AuthContext';

// Mock the API service
jest.mock('../../services/api', () => ({
  apiService: {
    getCurrentUser: jest.fn(),
  },
}));

const TestComponent = () => {
  const { user, loading, isAuthenticated, isStaff } = useAuth();
  
  return (
    <div>
      <div data-testid="loading">{loading ? 'Loading' : 'Not Loading'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'Authenticated' : 'Not Authenticated'}</div>
      <div data-testid="staff">{isStaff ? 'Staff' : 'Not Staff'}</div>
      <div data-testid="username">{user?.username || 'No User'}</div>
    </div>
  );
};

const TestApp = () => (
  <BrowserRouter>
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  </BrowserRouter>
);

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Clear localStorage
    localStorage.clear();
  });

  it('shows loading state initially', () => {
    const { apiService } = require('../../services/api');
    apiService.getCurrentUser.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(<TestApp />);
    
    expect(screen.getByTestId('loading')).toHaveTextContent('Loading');
  });

  it('shows not authenticated when no token', async () => {
    const { apiService } = require('../../services/api');
    apiService.getCurrentUser.mockRejectedValue(new Error('No token'));

    render(<TestApp />);

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 100));
    });

    expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('Not Authenticated');
    expect(screen.getByTestId('staff')).toHaveTextContent('Not Staff');
    expect(screen.getByTestId('username')).toHaveTextContent('No User');
  });

  it('shows authenticated user when token is valid', async () => {
    const mockUser = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      is_active: true,
      is_staff: false,
      created_at: '2025-01-01T00:00:00',
    };

    const { apiService } = require('../../services/api');
    apiService.getCurrentUser.mockResolvedValue({ data: mockUser });

    // Set token in localStorage
    localStorage.setItem('access_token', 'valid_token');

    render(<TestApp />);

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 100));
    });

    expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('Authenticated');
    expect(screen.getByTestId('staff')).toHaveTextContent('Not Staff');
    expect(screen.getByTestId('username')).toHaveTextContent('testuser');
  });

  it('shows staff user correctly', async () => {
    const mockStaffUser = {
      id: 2,
      username: 'staffuser',
      email: 'staff@example.com',
      is_active: true,
      is_staff: true,
      created_at: '2025-01-01T00:00:00',
    };

    const { apiService } = require('../../services/api');
    apiService.getCurrentUser.mockResolvedValue({ data: mockStaffUser });

    localStorage.setItem('access_token', 'valid_token');

    render(<TestApp />);

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 100));
    });

    expect(screen.getByTestId('authenticated')).toHaveTextContent('Authenticated');
    expect(screen.getByTestId('staff')).toHaveTextContent('Staff');
    expect(screen.getByTestId('username')).toHaveTextContent('staffuser');
  });

  it('clears localStorage on getCurrentUser failure', async () => {
    const { apiService } = require('../../services/api');
    apiService.getCurrentUser.mockRejectedValue(new Error('Invalid token'));

    localStorage.setItem('access_token', 'invalid_token');
    localStorage.setItem('refresh_token', 'invalid_refresh');

    render(<TestApp />);

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 100));
    });

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });
});
