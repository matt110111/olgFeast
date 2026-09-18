import { vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import LoginForm from '../../Auth/LoginForm';
import { ThemeProvider } from '../../../contexts/ThemeContext';
const mocks = vi.hoisted(() => ({ login: vi.fn() }));
vi.mock('../../../contexts/AuthContext', () => ({ useAuth: () => ({ login: mocks.login }) }));
function show() { render(<MemoryRouter><ThemeProvider><LoginForm /></ThemeProvider></MemoryRouter>); }
beforeEach(() => { mocks.login.mockReset(); });
it('shows organizer guidance without published demo passwords', () => {
  show(); expect(screen.getByText('Use the account provided by your event organizer.')).toBeInTheDocument();
  expect(screen.queryByText('Demo Credentials')).not.toBeInTheDocument();
  expect(screen.getByLabelText('Username')).toHaveAttribute('autoComplete', 'username');
});
it('submits credentials and prevents repeated clicks while pending', async () => {
  mocks.login.mockImplementation(() => new Promise(() => {})); show();
  fireEvent.change(screen.getByLabelText('Username'), {target:{value:'station1'}});
  fireEvent.change(screen.getByLabelText('Password'), {target:{value:'long-password'}});
  fireEvent.click(screen.getByRole('button',{name:'Sign in'}));
  await waitFor(() => expect(mocks.login).toHaveBeenCalledWith({username:'station1',password:'long-password'}));
  expect(screen.getByRole('button',{name:'Signing in...'})).toBeDisabled();
});
it('shows server login errors', async () => {
  mocks.login.mockRejectedValue({response:{data:{detail:'Account disabled'}}}); show();
  fireEvent.change(screen.getByLabelText('Username'), {target:{value:'station1'}});
  fireEvent.change(screen.getByLabelText('Password'), {target:{value:'long-password'}});
  fireEvent.click(screen.getByRole('button',{name:'Sign in'}));
  expect(await screen.findByText('Account disabled')).toBeInTheDocument();
});
