"use client";

import React, { useEffect, useState, useRef, useMemo, useCallback } from "react";
import { io, Socket } from "socket.io-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessageSquare, Users, Settings, Hash, Bot, Loader2, Send, AlertTriangle, Copy, Check, RefreshCw } from "lucide-react";

// ⚡ Bolt Optimization: Extract individual message item into a memoized component.
// When a new message is appended to the list, React will reuse the rendered output
// of existing messages instead of re-rendering all of them, changing O(N) to O(1).
const MessageItem = React.memo(({ msg }: { msg: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(msg).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch((err) => {
      console.error("Failed to copy message: ", err);
    });
  };

  return (
    <div className="group relative flex items-start gap-4">
      <div className="w-8 h-8 rounded bg-neutral-800 flex items-center justify-center shrink-0">
        <Users className="w-4 h-4 text-neutral-400" aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1 relative pr-10">
        <div className="flex items-baseline gap-2">
          <span className="font-medium text-sm">User</span>
          <time className="text-xs text-neutral-500">Just now</time>
        </div>
        <p className="text-neutral-300 mt-1 whitespace-pre-wrap break-words">{msg}</p>

        <Button
          onClick={handleCopy}
          variant="ghost"
          size="icon"
          className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity h-8 w-8 text-neutral-400 hover:text-white hover:bg-neutral-800"
          aria-label={copied ? "Copied" : "Copy message"}
          title={copied ? "Copied" : "Copy message"}
        >
          {copied ? (
            <Check className="w-4 h-4 text-green-500" aria-hidden="true" />
          ) : (
            <Copy className="w-4 h-4" aria-hidden="true" />
          )}
        </Button>
        <span aria-live="polite" className="sr-only">
          {copied ? "Message copied to clipboard" : ""}
        </span>
      </div>
    </div>
  );
});
MessageItem.displayName = 'MessageItem';

// ⚡ Bolt Optimization: Wrap MessageList in React.memo to prevent unnecessary re-renders
// of the entire message history on every keystroke in the message input field.
const MessageList = React.memo(({ messages }: { messages: string[] }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <>
      {messages.map((msg, idx) => (
        <MessageItem key={idx} msg={msg} />
      ))}
      <div ref={messagesEndRef} />
    </>
  );
});
MessageList.displayName = 'MessageList';

interface Workspace {
  id: string;
  name: string;
}

interface Agent {
  id: string;
  name: string;
  provider: string;
}

// ⚡ Bolt Optimization: Extract workspace items into a memoized component.
// This ensures that when activeWorkspace changes, only the previously active
// and newly active WorkspaceItem components re-render, rather than the entire list.
const WorkspaceItem = React.memo(({ ws, isActive, onClick }: { ws: Workspace; isActive: boolean; onClick: (ws: Workspace) => void }) => {
  return (
    <button
      onClick={() => onClick(ws)}
      className={`flex items-center w-full text-left gap-2 px-2 py-1.5 rounded-md cursor-pointer text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-600 ${
        isActive
          ? "bg-neutral-800 text-white"
          : "hover:bg-neutral-800/50 text-neutral-400"
      }`}
      aria-current={isActive ? "true" : undefined}
      title={ws.name}
    >
      <Hash className="w-4 h-4 shrink-0" aria-hidden="true" />
      <span className="truncate">{ws.name}</span>
    </button>
  );
});
WorkspaceItem.displayName = 'WorkspaceItem';

// ⚡ Bolt Optimization: Extract MessageInput to its own component so that typing
// doesn't trigger a re-render of the entire Home component (and Sidebar).
const MessageInput = React.memo(({ onSendMessage, disabled, isLoading, workspaceName }: { onSendMessage: (msg: string) => void, disabled: boolean, isLoading?: boolean, workspaceName?: string }) => {
  const [message, setMessage] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Focus input on '/' key if not already focusing an input
      if (
        e.key === "/" &&
        document.activeElement?.tagName !== "INPUT" &&
        document.activeElement?.tagName !== "TEXTAREA" &&
        !disabled
      ) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [disabled]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage("");
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      inputRef.current?.blur();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative flex items-center">
      <Input
        id="message-input"
        ref={inputRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleInputKeyDown}
        placeholder={isLoading ? "Loading..." : disabled ? "Select a workspace to message..." : workspaceName ? `Message #${workspaceName}...` : "Message @agents or team..."}
        className="w-full bg-neutral-800 border-neutral-700 text-white placeholder:text-neutral-500 pr-24 focus-visible:ring-1 focus-visible:ring-neutral-600 peer"
        disabled={disabled}
        aria-label={workspaceName ? `Message in ${workspaceName} workspace` : "Message input"}
        aria-keyshortcuts="/"
      />
      {!disabled && !message && (
        <kbd aria-hidden="true" className="absolute right-12 pointer-events-none peer-focus:opacity-0 transition-opacity duration-200 hidden sm:inline-flex h-5 items-center gap-1 rounded border border-neutral-700 bg-neutral-800 px-1.5 font-mono text-[10px] font-medium text-neutral-500">
          <span className="text-xs">/</span>
        </kbd>
      )}
      {!disabled && message.trim() && (
        <kbd aria-hidden="true" className="absolute right-12 pointer-events-none opacity-0 peer-focus:opacity-100 transition-opacity duration-200 hidden sm:inline-flex h-5 items-center gap-1 rounded border border-neutral-700 bg-neutral-800 px-1.5 font-mono text-[10px] font-medium text-neutral-500">
          Enter ↵
        </kbd>
      )}
      <Button
        type="submit"
        size="icon"
        variant="ghost"
        className="absolute right-1 top-1 h-8 w-8 text-neutral-400 hover:text-white hover:bg-neutral-700 disabled:opacity-50 disabled:hover:bg-transparent disabled:hover:text-neutral-400"
        disabled={!message.trim() || disabled}
        aria-label="Send message"
        title={isLoading ? "Loading..." : disabled ? "Select a workspace to send messages" : !message.trim() ? "Type a message to send" : "Send message"}
      >
        <Send className="w-4 h-4" aria-hidden="true" />
      </Button>
    </form>
  );
});
MessageInput.displayName = 'MessageInput';

export default function Home() {
  const socketRef = useRef<Socket | null>(null);
  const [messages, setMessages] = useState<string[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    // ⚡ Bolt Optimization: Use Promise.all to fetch workspaces and agents concurrently,
    // reducing initial load time and preventing sequential blocking.
    const fetchData = async () => {
      try {
        const token = localStorage.getItem("token") || "";
        const headers = {
          "Authorization": `Bearer ${token}`
        };

        const [wsRes, agentRes] = await Promise.all([
          fetch(`${apiUrl}/workspaces`, { headers }),
          fetch(`${apiUrl}/agents`, { headers })
        ]);

        if (!wsRes.ok || !agentRes.ok) {
          throw new Error("Failed to fetch data from API");
        }

        const wsData: unknown = await wsRes.json();
        const agentData: unknown = await agentRes.json();

        const workspacesList = (Array.isArray(wsData) ? wsData : []) as Workspace[];
        const agentsList = (Array.isArray(agentData) ? agentData : []) as Agent[];

        setWorkspaces(workspacesList);
        if (workspacesList.length > 0) {
          setActiveWorkspace(workspacesList[0]);
        }
        setAgents(agentsList);
        setError(null);
      } catch (err) {
        console.error("Error fetching data:", err);
        setError(err instanceof Error ? err.message : "Failed to load workspace data");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [apiUrl]);

  useEffect(() => {
    if (activeWorkspace) {
      document.title = `${activeWorkspace.name} | The Union`;
    }
  }, [activeWorkspace]);

  useEffect(() => {
    const activeWorkspaceId = activeWorkspace?.id;
    if (!activeWorkspaceId) return;

    // Connect to FastAPI backend
    const newSocket = io(apiUrl, {
      transports: ["websocket"],
    });

    newSocket.on("connect", () => {
      console.log("Connected to WebSocket");
      newSocket.emit("join_workspace", { workspace_id: activeWorkspaceId, token: localStorage.getItem("token") || "" });
    });

    newSocket.on("message", (data) => {
      setMessages((prev) => [...prev, data.msg]);
    });

    newSocket.on("chat_update", (data) => {
      setMessages((prev) => [...prev, data.msg]);
    });

    socketRef.current = newSocket;

    return () => {
      newSocket.close();
    };
  }, [apiUrl, activeWorkspace?.id]);

  // ⚡ Bolt Optimization: Wrap event handler in useCallback so its reference remains stable.
  // This prevents the memoized MessageInput from re-rendering needlessly.
  const handleSendMessage = useCallback((msg: string) => {
    if (socketRef.current && activeWorkspace) {
      socketRef.current.emit("chat_message", { workspace_id: activeWorkspace.id, message: msg, token: localStorage.getItem("token") || "" });
    }
  }, [activeWorkspace]);

  // ⚡ Bolt Optimization: Wrap workspace selection handler in useCallback
  // to pass a stable reference down to the memoized WorkspaceItem components.
  const handleWorkspaceClick = useCallback((ws: Workspace) => {
    setActiveWorkspace(ws);
  }, []);

  // ⚡ Bolt Optimization: Isolate the agents mapping into its own useMemo block.
  // This ensures the agent list (which doesn't depend on activeWorkspace) doesn't
  // re-evaluate when the user merely switches between workspaces.
  const agentsListContent = useMemo(() => {
    if (isLoading) {
      return ["w-full", "w-11/12", "w-5/6"].map((width, i) => (
        <div key={i} className={`h-9 bg-neutral-800/50 rounded-md animate-pulse ${width}`}><span className="sr-only">Loading...</span></div>
      ));
    }
    if (error) {
      return <div className="flex items-center gap-2 text-sm text-red-400 px-2 py-2 bg-red-950/30 rounded-md border border-red-900/50"><AlertTriangle className="w-4 h-4 shrink-0" aria-hidden="true" /><span>Error loading agents</span></div>;
    }
    if (agents.length === 0) {
      return <div className="flex flex-col items-center justify-center py-4 px-2 border border-dashed border-neutral-800 rounded-md bg-neutral-800/20 text-center"><Bot className="w-5 h-5 text-neutral-600 mb-2" aria-hidden="true" /><span className="text-xs text-neutral-500">No agents available</span></div>;
    }
    return agents.map((agent) => (
      <div
        key={agent.id}
        className="group flex items-center justify-between w-full text-left px-2 py-1.5 hover:bg-neutral-800/50 rounded-md"
        title={agent.name}
      >
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-6 h-6 shrink-0 rounded bg-blue-600 flex items-center justify-center transition-transform group-hover:scale-110">
            <Bot className="w-3 h-3 text-white" aria-hidden="true" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-sm truncate">{agent.name}</span>
            <span className="text-[10px] text-neutral-500 truncate leading-none" title={agent.provider}>{agent.provider}</span>
          </div>
        </div>
        <span className="sr-only">Online</span>
        <div aria-hidden="true" className="w-2 h-2 shrink-0 rounded-full bg-green-500 ml-2"></div>
      </div>
    ));
  }, [agents, isLoading, error]);

  // ⚡ Bolt Optimization: Memoize the Sidebar to prevent its expensive loops (workspaces.map and agents.map)
  // from re-evaluating every time a new chat message arrives (which updates `messages` state and triggers Home re-render).
  const sidebarContent = useMemo(() => {
    return (
      <aside className="w-64 bg-neutral-950 border-r border-neutral-800 flex flex-col" aria-label="Sidebar navigation">
        <div className="p-4 border-b border-neutral-800 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">The Union</h1>
          <button aria-label="Settings" title="Settings" className="text-neutral-400 hover:text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-600 rounded-md">
            <Settings className="w-5 h-5 cursor-pointer" aria-hidden="true" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <div className="px-4 mb-6">
            <h2 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-3">Workspaces</h2>
            <div className="space-y-1">
              {isLoading ? (
                ["w-full", "w-11/12", "w-5/6"].map((width, i) => (
                  <div key={i} className={`h-8 bg-neutral-800/50 rounded-md animate-pulse ${width}`}><span className="sr-only">Loading...</span></div>
                ))
              ) : error ? (
                <div className="flex items-center gap-2 text-sm text-red-400 px-2 py-2 bg-red-950/30 rounded-md border border-red-900/50"><AlertTriangle className="w-4 h-4 shrink-0" aria-hidden="true" /><span>Error loading workspaces</span></div>
              ) : workspaces.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-4 px-2 border border-dashed border-neutral-800 rounded-md bg-neutral-800/20 text-center"><Hash className="w-5 h-5 text-neutral-600 mb-2" aria-hidden="true" /><span className="text-xs text-neutral-500">No workspaces</span></div>
              ) : (
                workspaces.map((ws) => (
                  <WorkspaceItem
                    key={ws.id}
                    ws={ws}
                    isActive={activeWorkspace?.id === ws.id}
                    onClick={handleWorkspaceClick}
                  />
                ))
              )}
            </div>
          </div>

          <div className="px-4">
            <h2 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-3">AI Pool</h2>
            <div className="space-y-2">
              {agentsListContent}
            </div>
          </div>
        </div>
      </aside>
    );
  }, [isLoading, error, workspaces, activeWorkspace?.id, handleWorkspaceClick, agentsListContent]);

  return (
    <div className="flex h-screen bg-neutral-900 text-white font-sans">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-neutral-900 focus:text-white">Skip to main content</a>
      {/* Sidebar */}
      {sidebarContent}

      {/* Main Chat Area */}
      <main id="main-content" tabIndex={-1} className="flex-1 flex flex-col bg-neutral-900 outline-none" aria-label="Main chat area">
        <div className="h-14 border-b border-neutral-800 flex items-center px-6">
          <h2 className="font-semibold flex items-center gap-2 min-w-0">
            <Hash className="w-5 h-5 text-neutral-400 shrink-0" aria-hidden="true" />
            {isLoading ? (
              <div className="h-5 w-32 bg-neutral-800 rounded animate-pulse"><span className="sr-only">Loading...</span></div>
            ) : (
              <span className="truncate" title={activeWorkspace?.name || "Select a Workspace"}>
                {activeWorkspace?.name || "Select a Workspace"}
              </span>
            )}
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4 flex flex-col focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neutral-600 focus-visible:ring-inset" role="log" aria-live="polite" aria-label="Message history" tabIndex={0}>
          {isLoading ? (
            <div className="flex-1 flex flex-col items-center justify-center text-neutral-500 space-y-4 my-auto">
              <Loader2 className="w-8 h-8 text-neutral-400 animate-spin" aria-hidden="true" />
              <span className="sr-only">Loading workspace data...</span>
            </div>
          ) : error ? (
            <div className="flex-1 flex flex-col items-center justify-center text-red-500 space-y-4 my-auto">
              <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-500" aria-hidden="true" />
              </div>
              <div className="text-center max-w-md space-y-4">
                <div>
                  <p className="text-lg font-medium" role="alert">Connection Error</p>
                  <p className="text-sm text-red-400 mb-2">{error}</p>
                  <p className="text-sm text-neutral-400">Please check your network connection or try refreshing the page.</p>
                </div>
                <Button
                  onClick={() => window.location.reload()}
                  variant="outline"
                  className="border-neutral-700 bg-transparent text-neutral-300 hover:text-white hover:bg-neutral-800"
                >
                  <RefreshCw className="w-4 h-4 mr-2" aria-hidden="true" />
                  Try Again
                </Button>
              </div>
            </div>
          ) : !activeWorkspace ? (
            <div className="flex-1 flex flex-col items-center justify-center text-neutral-500 space-y-4 my-auto">
              <div className="w-12 h-12 rounded-full bg-neutral-800 flex items-center justify-center">
                <Hash className="w-6 h-6 text-neutral-400" aria-hidden="true" />
              </div>
              <div className="text-center">
                <p className="text-lg font-medium text-neutral-300">No workspace selected</p>
                <p className="text-sm">Choose a workspace from the sidebar to start messaging</p>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-neutral-500 space-y-4 my-auto">
              <div className="w-12 h-12 rounded-full bg-neutral-800 flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-neutral-400" aria-hidden="true" />
              </div>
              <div className="text-center max-w-md space-y-4">
                <div>
                  <p className="text-lg font-medium text-neutral-300">No messages yet</p>
                  <p className="text-sm mb-4">Start the conversation in {activeWorkspace.name}</p>
                </div>
                <Button
                  onClick={() => {
                    handleSendMessage("Hello! 👋");
                    setTimeout(() => document.getElementById("message-input")?.focus(), 0);
                  }}
                  variant="outline"
                  className="border-neutral-700 bg-transparent text-neutral-300 hover:text-white hover:bg-neutral-800"
                >
                  <MessageSquare className="w-4 h-4 mr-2" aria-hidden="true" />
                  Say Hello
                </Button>
              </div>
            </div>
          ) : (
            <MessageList messages={messages} />
          )}
        </div>

        <div className="p-4 px-6 pb-6">
          <MessageInput onSendMessage={handleSendMessage} disabled={!activeWorkspace || isLoading} isLoading={isLoading} workspaceName={activeWorkspace?.name} />
        </div>
      </main>
    </div>
  );
}
