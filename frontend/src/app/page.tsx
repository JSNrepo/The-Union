"use client";

import React, { useEffect, useState, useRef } from "react";
import { io, Socket } from "socket.io-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessageSquare, Users, Settings, Hash, Bot } from "lucide-react";

// ⚡ Bolt Optimization: Wrap MessageList in React.memo to prevent unnecessary re-renders
// of the entire message history on every keystroke in the message input field.
const MessageList = React.memo(({ messages }: { messages: string[] }) => {
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

export default function Home() {
  const socketRef = useRef<Socket | null>(null);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<string[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    // Fetch initial data
    const fetchData = async () => {
      try {
        const wsRes = await fetch(`${apiUrl}/workspaces`);
        const wsData: Workspace[] = await wsRes.json();
        setWorkspaces(wsData);
        if (wsData.length > 0) {
          setActiveWorkspace(wsData[0]);
        }

        const agentRes = await fetch(`${apiUrl}/agents`);
        const agentData: Agent[] = await agentRes.json();
        setAgents(agentData);
      } catch (err) {
        console.error("Error fetching data:", err);
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

  const sendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (socketRef.current && message.trim() && activeWorkspace) {
      socketRef.current.emit("chat_message", { workspace_id: activeWorkspace.id, message });
      setMessage("");
    }
  };

  return (
    <div className="flex h-screen bg-neutral-900 text-white font-sans">
      {/* Sidebar */}
      <div className="w-64 bg-neutral-950 border-r border-neutral-800 flex flex-col">
        <div className="p-4 border-b border-neutral-800 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">The Union</h1>
          <button aria-label="Settings" className="text-neutral-400 hover:text-white transition-colors">
            <Settings className="w-5 h-5 cursor-pointer" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <div className="px-4 mb-6">
            <h2 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-3">Workspaces</h2>
            <div className="space-y-1">
              {workspaces.map((ws) => (
                <div
                  key={ws.id}
                  onClick={() => setActiveWorkspace(ws)}
                  className={`flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer text-sm ${
                    activeWorkspace?.id === ws.id
                      ? "bg-neutral-800 text-white"
                      : "hover:bg-neutral-800/50 text-neutral-400"
                  }`}
                >
                  <Hash className="w-4 h-4" />
                  <span>{ws.name}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="px-4">
            <h2 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-3">AI Pool</h2>
            <div className="space-y-2">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className="flex items-center justify-between px-2 py-1.5 hover:bg-neutral-800/50 rounded-md cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded bg-blue-600 flex items-center justify-center">
                      <Bot className="w-3 h-3 text-white" />
                    </div>
                    <span className="text-sm">{agent.name}</span>
                  </div>
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-neutral-900">
        <div className="h-14 border-b border-neutral-800 flex items-center px-6">
          <h2 className="font-semibold flex items-center gap-2">
            <Hash className="w-5 h-5 text-neutral-400" />
            {activeWorkspace?.name || "Loading..."}
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <MessageList messages={messages} />
        </div>

        <div className="p-4 px-6 pb-6">
          <form onSubmit={sendMessage} className="relative">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Message @agents or team..."
              className="w-full bg-neutral-800 border-neutral-700 text-white placeholder:text-neutral-500 pr-12 focus-visible:ring-1 focus-visible:ring-neutral-600"
            />
            <Button
              type="submit"
              size="icon"
              variant="ghost"
              className="absolute right-1 top-1 h-8 w-8 text-neutral-400 hover:text-white hover:bg-neutral-700 disabled:opacity-50 disabled:hover:bg-transparent disabled:hover:text-neutral-400"
              disabled={!message.trim()}
              aria-label="Send message"
            >
              <MessageSquare className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
