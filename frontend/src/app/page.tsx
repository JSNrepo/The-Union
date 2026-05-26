"use client";

import React, { useEffect, useState, useRef, useMemo, useCallback } from "react";
import { io, Socket } from "socket.io-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessageSquare, Users, Settings, Hash, Bot, Loader2 } from "lucide-react";

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
        <div key={idx} className="flex items-start gap-4">
          <div className="w-8 h-8 rounded bg-neutral-800 flex items-center justify-center shrink-0">
            <Users className="w-4 h-4 text-neutral-400" />
          </div>
          <div>
            <div className="flex items-baseline gap-2">
              <span className="font-medium text-sm">User</span>
              <span className="text-xs text-neutral-500">Just now</span>
            </div>
            <p className="text-neutral-300 mt-1">{msg}</p>
          </div>
        </div>
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

// ⚡ Bolt Optimization: Extract MessageInput to its own component so that typing
// doesn't trigger a re-render of the entire Home component (and Sidebar).
const MessageInput = React.memo(({ onSendMessage, disabled }: { onSendMessage: (msg: string) => void, disabled: boolean }) => {
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

      // Blur input on Escape key
      if (e.key === "Escape" && document.activeElement === inputRef.current) {
        inputRef.current?.blur();
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
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative flex items-center">
      <Input
        ref={inputRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder={disabled ? "Select a workspace to message..." : "Message @agents or team..."}
        className="w-full bg-neutral-800 border-neutral-700 text-white placeholder:text-neutral-500 pr-24 focus-visible:ring-1 focus-visible:ring-neutral-600"
        disabled={disabled}
        aria-label="Message input"
      />
      <div className="absolute right-12 flex items-center pointer-events-none">
        {!disabled && !message && (
          <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border border-neutral-700 bg-neutral-800 px-1.5 font-mono text-[10px] font-medium text-neutral-500 opacity-100">
            <span className="text-xs">/</span>
          </kbd>
        )}
      </div>
      <Button
        type="submit"
        size="icon"
        variant="ghost"
        className="absolute right-1 top-1 h-8 w-8 text-neutral-400 hover:text-white hover:bg-neutral-700 disabled:opacity-50 disabled:hover:bg-transparent disabled:hover:text-neutral-400"
        disabled={!message.trim() || disabled}
        aria-label="Send message"
        title={disabled ? "Select a workspace to send messages" : !message.trim() ? "Type a message to send" : "Send message"}
      >
        <MessageSquare className="w-4 h-4" />
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
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    // ⚡ Bolt Optimization: Use Promise.all to fetch workspaces and agents concurrently,
    // reducing initial load time and preventing sequential blocking.
    const fetchData = async () => {
      try {
        const [wsRes, agentRes] = await Promise.all([
          fetch(`${apiUrl}/workspaces`),
          fetch(`${apiUrl}/agents`)
        ]);

        if (!wsRes.ok || !agentRes.ok) {
          throw new Error("Failed to fetch data from API");
        }

        const wsData: any = await wsRes.json();
        const agentData: any = await agentRes.json();

        const workspacesList = Array.isArray(wsData) ? wsData : [];
        const agentsList = Array.isArray(agentData) ? agentData : [];

        setWorkspaces(workspacesList);
        if (workspacesList.length > 0) {
          setActiveWorkspace(workspacesList[0]);
        }
        setAgents(agentsList);
      } catch (err) {
        console.error("Error fetching data:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [apiUrl]);

  useEffect(() => {
    if (!activeWorkspace) return;

    // Connect to FastAPI backend
    const newSocket = io(apiUrl, {
      transports: ["websocket"],
    });

    newSocket.on("connect", () => {
      console.log("Connected to WebSocket");
      newSocket.emit("join_workspace", { workspace_id: activeWorkspace.id });
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
  }, [apiUrl, activeWorkspace, activeWorkspace?.id]);

  // ⚡ Bolt Optimization: Wrap event handler in useCallback so its reference remains stable.
  // This prevents the memoized MessageInput from re-rendering needlessly.
  const handleSendMessage = useCallback((msg: string) => {
    if (socketRef.current && activeWorkspace) {
      socketRef.current.emit("chat_message", { workspace_id: activeWorkspace.id, message: msg });
    }
  }, [activeWorkspace]);

  // ⚡ Bolt Optimization: Memoize the Sidebar to prevent its expensive loops (workspaces.map and agents.map)
  // from re-evaluating every time a new chat message arrives (which updates `messages` state and triggers Home re-render).
  const sidebarContent = useMemo(() => {
    return (
      <aside className="w-64 bg-neutral-950 border-r border-neutral-800 flex flex-col" aria-label="Sidebar navigation">
        <div className="p-4 border-b border-neutral-800 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">The Union</h1>
          <button aria-label="Settings" title="Settings" className="text-neutral-400 hover:text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-600 rounded-md">
            <Settings className="w-5 h-5 cursor-pointer" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <div className="px-4 mb-6">
            <h2 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-3">Workspaces</h2>
            <div className="space-y-1">
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-8 bg-neutral-800/50 rounded-md animate-pulse"></div>
                ))
              ) : workspaces.length === 0 ? (
                <div className="text-sm text-neutral-500 px-2 py-1.5">No workspaces found</div>
              ) : (
                workspaces.map((ws) => (
                <button
                  key={ws.id}
                  onClick={() => setActiveWorkspace(ws)}
                  className={`flex items-center w-full text-left gap-2 px-2 py-1.5 rounded-md cursor-pointer text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-600 ${
                    activeWorkspace?.id === ws.id
                      ? "bg-neutral-800 text-white"
                      : "hover:bg-neutral-800/50 text-neutral-400"
                  }`}
                  aria-current={activeWorkspace?.id === ws.id ? "true" : undefined}
                >
                  <Hash className="w-4 h-4 shrink-0" />
                  <span className="truncate">{ws.name}</span>
                </button>
                ))
              )}
            </div>
          </div>

          <div className="px-4">
            <h2 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-3">AI Pool</h2>
            <div className="space-y-2">
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-9 bg-neutral-800/50 rounded-md animate-pulse"></div>
                ))
              ) : agents.length === 0 ? (
                <div className="text-sm text-neutral-500 px-2 py-1.5">No agents available</div>
              ) : (
                agents.map((agent) => (
                <button
                  key={agent.id}
                  className="flex items-center justify-between w-full text-left px-2 py-1.5 hover:bg-neutral-800/50 rounded-md cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-600"
                >
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded bg-blue-600 flex items-center justify-center">
                      <Bot className="w-3 h-3 text-white" />
                    </div>
                    <span className="text-sm">{agent.name}</span>
                  </div>
                  <span className="sr-only">Online</span>
                  <div aria-hidden="true" className="w-2 h-2 rounded-full bg-green-500"></div>
                </button>
                ))
              )}
            </div>
          </div>
        </div>
      </aside>
    );
  }, [isLoading, workspaces, agents, activeWorkspace?.id]);

  return (
    <div className="flex h-screen bg-neutral-900 text-white font-sans">
      {/* Sidebar */}
      {sidebarContent}

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col bg-neutral-900" aria-label="Main chat area">
        <div className="h-14 border-b border-neutral-800 flex items-center px-6">
          <h2 className="font-semibold flex items-center gap-2">
            <Hash className="w-5 h-5 text-neutral-400" />
            {activeWorkspace?.name || "Select a Workspace"}
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4 flex flex-col" role="log" aria-live="polite">
          {isLoading ? (
            <div className="flex-1 flex flex-col items-center justify-center text-neutral-500 space-y-4 my-auto">
              <Loader2 className="w-8 h-8 text-neutral-400 animate-spin" />
              <span className="sr-only">Loading workspace data...</span>
            </div>
          ) : !activeWorkspace ? (
            <div className="flex-1 flex flex-col items-center justify-center text-neutral-500 space-y-4 my-auto">
              <div className="w-12 h-12 rounded-full bg-neutral-800 flex items-center justify-center">
                <Hash className="w-6 h-6 text-neutral-400" />
              </div>
              <div className="text-center">
                <p className="text-lg font-medium text-neutral-300">No workspace selected</p>
                <p className="text-sm">Choose a workspace from the sidebar to start messaging</p>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-neutral-500 space-y-4 my-auto">
              <div className="w-12 h-12 rounded-full bg-neutral-800 flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-neutral-400" />
              </div>
              <div className="text-center">
                <p className="text-lg font-medium text-neutral-300">No messages yet</p>
                <p className="text-sm">Start the conversation in {activeWorkspace.name}</p>
              </div>
            </div>
          ) : (
            <MessageList messages={messages} />
          )}
        </div>

        <div className="p-4 px-6 pb-6">
          <MessageInput onSendMessage={handleSendMessage} disabled={!activeWorkspace} />
        </div>
      </main>
    </div>
  );
}
