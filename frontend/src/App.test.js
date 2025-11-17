import { render, screen, waitFor } from '@testing-library/react';
import axios from 'axios';
import App from './App';

jest.mock('axios');

test('renders draft assistant header and tabs', async () => {
  axios.post.mockResolvedValue({ data: { slots: [], win_projection: null } });
  axios.get.mockResolvedValue({ data: {} });
  render(<App />);
  expect(screen.getByText(/LoL Draft Analyzer/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Draft Assistant/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Coach Test/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Health/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /PRO Order/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /SoloQ Simultaneous/i })).toBeInTheDocument();
  expect(screen.getByPlaceholderText(/Search champion to ban/i)).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText(/^Ban Turn:/i)).toBeInTheDocument());
  expect(axios.post).toHaveBeenCalledTimes(1);
  const [url, payload] = axios.post.mock.calls[0];
  expect(url).toBe('http://localhost:8000/draft/bans');
  expect(payload).toMatchObject({ team: 'blue', mode: 'pro' });
});
