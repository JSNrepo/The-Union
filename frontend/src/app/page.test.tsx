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
      // @ts-expect-error Mock implementation

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
      // @ts-expect-error Mock implementation

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
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });

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

  it('handles connect event and emits join_workspace', async () => {
    let connectCallback: () => void = () => {};
    const mockEmit = vi.fn();

    const mockIo = vi.mocked(io);
    mockIo.mockReturnValue({
      ...vi.mocked(io)(),
      // @ts-expect-error Mock implementation
      on: vi.fn((event, callback) => {
        if (event === 'connect') {
          connectCallback = callback;
        }
      }),
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
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });

    act(() => {
      connectCallback();
    });

    expect(mockEmit).toHaveBeenCalledWith('join_workspace', {
      workspace_id: mockWorkspaces[0].id, // General is the default
      token: 'mock-token'
    });
  });

  it('simulates receiving a chat_update message', async () => {
    let chatUpdateCallback: (data: { msg: string }) => void = () => {};

    const mockIo = vi.mocked(io);
    mockIo.mockReturnValue({
      ...vi.mocked(io)(),
      // @ts-expect-error Mock implementation
      on: vi.fn((event, callback) => {
        if (event === 'chat_update') {
          chatUpdateCallback = callback;
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

    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });

    act(() => {
      chatUpdateCallback({ msg: 'Agent typing...' });
    });

    // After receiving chat_update, the message is added to state, but we need
    // an act() block for React to flush the effect (auto-scroll) correctly.
    await act(async () => {
      await new Promise((r) => setTimeout(r, 0));
    });

    await waitFor(() => {
        expect(screen.getByText('Agent typing...')).toBeInTheDocument();
    }, { timeout: 2000 });
});


  it('handles input escape key blur', async () => {
    (global.fetch as Mock).mockImplementation((url: string) => {
      if (url.includes('/workspaces')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockWorkspaces) });
      if (url.includes('/agents')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgents) });
      return Promise.reject(new Error('not found'));
    });

    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });

    const engWorkspaceButton = screen.getByText('Engineering');
    fireEvent.click(engWorkspaceButton);


    const input = screen.getByPlaceholderText('Message #Engineering...');
    input.focus();
    expect(input).toHaveFocus();

    fireEvent.keyDown(input, { key: 'Escape', code: 'Escape' });
    expect(input).not.toHaveFocus();
  });


  it('prevents sending empty messages', async () => {
    (global.fetch as Mock).mockImplementation((url: string) => {
      if (url.includes('/workspaces')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockWorkspaces) });
      if (url.includes('/agents')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgents) });
      return Promise.reject(new Error('not found'));
    });

    const mockEmit = vi.fn();
    const mockIo = vi.mocked(io);
    mockIo.mockReturnValue({
      ...vi.mocked(io)(),
      emit: mockEmit,
    });

    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });

    const button = screen.getByText('Engineering');
    fireEvent.click(button);
    const input = screen.getByPlaceholderText('Message #Engineering...');
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.submit(input);

    expect(mockEmit).not.toHaveBeenCalledWith('message', expect.anything());
  });

  it('allows switching workspaces', async () => {
    (global.fetch as Mock).mockImplementation((url: string) => {
      if (url.includes('/workspaces')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockWorkspaces) });
      if (url.includes('/agents')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgents) });
      return Promise.reject(new Error('not found'));
    });

    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });

    const engWorkspaceButton = screen.getByText('Engineering');
    fireEvent.click(engWorkspaceButton);

    await waitFor(() => {
      expect(document.title).toBe('Engineering | The Union');
    });
  });

  it('reloads window on Try Again click', async () => {
    const originalLocation = window.location;
    // @ts-expect-error Mock implementation
    delete window.location;
    window.location = { ...originalLocation, reload: vi.fn() };

    (global.fetch as Mock).mockRejectedValueOnce(new Error('Network failure'));
    render(<Home />);

    await waitFor(() => {
      expect(screen.getByText('Connection Error')).toBeInTheDocument();
    });

    const tryAgainButton = screen.getByRole('button', { name: /try again/i });
    fireEvent.click(tryAgainButton);

    expect(window.location.reload).toHaveBeenCalled();

    window.location = originalLocation;
  });

  it('handles api fetch returning not ok', async () => {
    (global.fetch as Mock).mockResolvedValueOnce({ ok: false });
    (global.fetch as Mock).mockResolvedValueOnce({ ok: false });
    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Connection Error')).toBeInTheDocument();
    });
  });

  it('displays no agents available when agents list is empty', async () => {
    (global.fetch as Mock).mockImplementation((url: string) => {
      if (url.includes('/workspaces')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockWorkspaces) });
      if (url.includes('/agents')) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      return Promise.reject(new Error('not found'));
    });
    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('No agents available')).toBeInTheDocument();
    });
  });

  it('sends message via MessageInput form submission', async () => {
    const mockEmit = vi.fn();
    const mockIo = vi.mocked(io);
    mockIo.mockReturnValue({
      ...vi.mocked(io)(),
      emit: mockEmit,
    } as unknown);

    (global.fetch as Mock).mockImplementation((url: string) => {
      if (url.includes('/workspaces')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockWorkspaces) });
      if (url.includes('/agents')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgents) });
      return Promise.reject(new Error('not found'));
    });

    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });

    const engWorkspaceButton = screen.getByText('Engineering');
    fireEvent.click(engWorkspaceButton);

    const input = screen.getByPlaceholderText('Message #Engineering...');
    fireEvent.change(input, { target: { value: 'Testing input' } });
    fireEvent.submit(input);

    expect(mockEmit).toHaveBeenCalledWith('chat_message', expect.objectContaining({
      workspace_id: '2',
      message: 'Testing input'
    }));
  });

  it('focuses input on / key press', async () => {
    (global.fetch as Mock).mockImplementation((url: string) => {
      if (url.includes('/workspaces')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockWorkspaces) });
      if (url.includes('/agents')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgents) });
      return Promise.reject(new Error('not found'));
    });

    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });

    const engWorkspaceButton = screen.getByText('Engineering');
    fireEvent.click(engWorkspaceButton);

    const input = screen.getByPlaceholderText('Message #Engineering...');
    expect(input).not.toHaveFocus();

    // Create an event that is cancelable so preventDefault can be called and tracked
    const event = new KeyboardEvent('keydown', { key: '/', code: 'Slash', bubbles: true, cancelable: true });
    const preventDefaultSpy = vi.spyOn(event, 'preventDefault');
    document.dispatchEvent(event);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(input).toHaveFocus();
  });

  it('logs error when clipboard fails to copy', async () => {
    const consoleErrorMock = vi.spyOn(console, 'error').mockImplementation(() => {});

    let messageCallback: (data: { msg: string }) => void = () => {};

    const mockIo = vi.mocked(io);
    mockIo.mockReturnValue({
      ...vi.mocked(io)(),
      // @ts-expect-error Mock implementation
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
      clipboard: { writeText: vi.fn().mockRejectedValue(new Error('Copy failed')) },
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
      expect(consoleErrorMock).toHaveBeenCalledWith("Failed to copy message: ", expect.any(Error));
    });

    consoleErrorMock.mockRestore();
  });

  it('connects to websocket and cleans up on unmount', async () => {
    const mockClose = vi.fn();
    const mockIo = vi.mocked(io);
    mockIo.mockReturnValue({
      ...vi.mocked(io)(),
      close: mockClose,
      on: vi.fn(),
      emit: vi.fn(),
    } as unknown);

    (global.fetch as Mock).mockImplementation((url: string) => {
      if (url.includes('/workspaces')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockWorkspaces) });
      if (url.includes('/agents')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgents) });
      return Promise.reject(new Error('not found'));
    });

    const { unmount } = render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });

    // Changing workspace should disconnect and reconnect
    const engWorkspaceButton = screen.getByText('Engineering');
    fireEvent.click(engWorkspaceButton);

    await waitFor(() => {
       expect(mockClose).toHaveBeenCalled();
    });

    unmount();

    expect(mockClose).toHaveBeenCalledTimes(2);
  });
});
