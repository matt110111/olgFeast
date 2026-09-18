import { vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';
vi.mock('./services/api', () => ({ apiService: { getFoodGroups: vi.fn().mockResolvedValue({data:[]}) } }));
it('renders the public menu route', async () => {
  window.history.replaceState({}, '', '/');
  render(<App />);
  expect(await screen.findByText('Our Menu')).toBeInTheDocument();
});
