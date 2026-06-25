import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import { io } from 'socket.io-client';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import Home from './page';

// Mock socket.io
vi.mock('socket.io-client', () => ({
  io: vi.fn(() => ({
    on: vi.fn(),
    emit: vi.fn(),
    close: vi.fn(),
  })),
}));

// Mock window.HTMLElement.prototype.scrollIntoView since it's not in jsdom
window.HTMLElement.prototype.scrollIntoView = vi.fn();

const mockWorkspaces = [{ id: '1', name: 'General' }, { id: '2', name: 'Engineering' }];
const mockAgents = [{ id: 'a1', name: 'Alice Claude', provider: 'claude' }];

describe('Home Page', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
    Storage.prototype.getItem = vi.fn(() => 'mock-token');
    // Ensure document title starts clean for each test
    document.title = '';
  });

  it('renders loading skeleton initially', async () => {
    (global.fetch as Mock).mockImplementation(() => new Promise(() => {})); // Never resolves
    render(<Home />);
    expect(screen.getByText('Loading workspace data...')).toBeInTheDocument();
  });

  it('handles network error state', async () => {
    (global.fetch as Mock).mockRejectedValueOnce(new Error('Network failure'));
    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Connection Error')).toBeInTheDocument();
    });
  });

  it('loads and displays workspaces and changes title', async () => {
    (global.fetch as Mock).mockImplementation((url: string) => {
      if (url.includes('/workspaces')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockWorkspaces) });
      if (url.includes('/agents')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgents) });
      return Promise.reject(new Error('not found'));
    });
    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });
    // Use waitFor for title change since it happens in a separate useEffect
    await waitFor(() => {
      expect(document.title).toBe('General | The Union');
    });
  });

  it('simulates receiving a message and copying to clipboard', async () => {
    let messageCallback: (data: { msg: string }) => void = () => {};

    const mockIo = vi.mocked(io);
    mockIo.mockReturnValue({
      ...vi.mocked(io)(),
      // @ts-ignore

      on: vi.fn((event, callback) => {
        if (event === 'message') {
          messageCallback = callback;
        }
      }),
      emit: vi.fn(),
      close: vi.fn(),
    });

    (global.fetch as Mock).mockImplementation((url: string) => {
      if (url.includes('/workspaces')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockWorkspaces) });
      if (url.includes('/agents')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgents) });
      return Promise.reject(new Error('not found'));
    });

    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });

    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });

    // Simulate receiving a message
    act(() => {
      messageCallback({ msg: 'Hello from socket' });
    });

    await waitFor(() => {
      expect(screen.getByText('Hello from socket')).toBeInTheDocument();
    });

    const copyButton = screen.getByRole('button', { name: 'Copy message' });
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Hello from socket');
    });
  });

  it('sends a message when input is submitted', async () => {
    const mockEmit = vi.fn();

    const mockIo = vi.mocked(io);
    mockIo.mockReturnValue({
      ...vi.mocked(io)(),
      // @ts-ignore

      on: vi.fn(),
      emit: mockEmit,
      close: vi.fn(),
    });

    (global.fetch as Mock).mockImplementation((url: string) => {
      if (url.includes('/workspaces')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockWorkspaces) });
      if (url.includes('/agents')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgents) });
      return Promise.reject(new Error('not found'));
    });

    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Say Hello')).toBeInTheDocument();
    });

    const sendButton = screen.getByText('Say Hello');
    fireEvent.click(sendButton);

    expect(mockEmit).toHaveBeenCalledWith('chat_message', expect.objectContaining({
      workspace_id: '1',
      message: 'Hello! 👋'
    }));
  });
});
