"use client";

import React, { useEffect, useState, useRef } from "react";
import { io, Socket } from "socket.io-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessageSquare, Users, Settings, Hash, Bot } from "lucide-react";

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

MessageList.displayName = "MessageList";

export default function Home() {
  const socketRef = useRef<Socket | null>(null);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<string[]>([]);
  const [workspaces, setWorkspaces] = useState<{ id: string; name: string }[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);

  useEffect(() => {
    // Fetch workspaces
    fetch("http://localhost:8000/workspaces")
      .then((res) => res.json())
      .then((data) => {
        setWorkspaces(data);
        if (data.length > 0) {
          setActiveWorkspaceId(data[0].id);
        }
      })
      .catch((err) => console.error("Failed to fetch workspaces", err));
  }, []);

  useEffect(() => {
    if (!activeWorkspaceId) return;

    // Connect to FastAPI backend
    const newSocket = io("http://localhost:8000", {
      transports: ["websocket"],
    });

    newSocket.on("connect", () => {
      console.log("Connected to WebSocket");
      newSocket.emit("join_workspace", { workspace_id: activeWorkspaceId });
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
      setMessages([]); // Clear messages on workspace switch
    };
  }, [activeWorkspaceId]);

  const sendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (socketRef.current && message.trim() && activeWorkspaceId) {
      socketRef.current.emit("chat_message", { workspace_id: activeWorkspaceId, message });
      setMessage("");
    }
  };

  return (
    <div className="flex h-screen bg-neutral-900 text-white font-sans">
      {/* Sidebar */}
      <div className="w-64 bg-neutral-950 border-r border-neutral-800 flex flex-col">
        <div className="p-4 border-b border-neutral-800 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">The Union</h1>
          <Settings className="w-5 h-5 text-neutral-400 cursor-pointer hover:text-white" />
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <div className="px-4 mb-6">
            <h2 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-3">Workspaces</h2>
            <div className="space-y-1">
              {workspaces.map((ws) => (
                <div
                  key={ws.id}
                  onClick={() => setActiveWorkspaceId(ws.id)}
                  className={`flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer text-sm ${
                    activeWorkspaceId === ws.id
                      ? "bg-neutral-800 text-white"
                      : "hover:bg-neutral-800/50 text-neutral-400"
                  }`}
                >
                  <Hash className="w-4 h-4 text-neutral-400" />
                  <span>{ws.name}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="px-4">
            <h2 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-3">AI Pool</h2>
            <div className="space-y-2">
              <div className="flex items-center justify-between px-2 py-1.5 hover:bg-neutral-800/50 rounded-md cursor-pointer">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded bg-blue-600 flex items-center justify-center">
                    <Bot className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-sm">Alice&apos;s Claude</span>
                </div>
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
              </div>
              <div className="flex items-center justify-between px-2 py-1.5 hover:bg-neutral-800/50 rounded-md cursor-pointer">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded bg-emerald-600 flex items-center justify-center">
                    <Bot className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-sm">Bob&apos;s Gemini</span>
                </div>
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-neutral-900">
        <div className="h-14 border-b border-neutral-800 flex items-center px-6">
          <h2 className="font-semibold flex items-center gap-2">
            <Hash className="w-5 h-5 text-neutral-400" />
            {workspaces.find((ws) => ws.id === activeWorkspaceId)?.name || "Select a Workspace"}
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
              className="absolute right-1 top-1 h-8 w-8 text-neutral-400 hover:text-white hover:bg-neutral-700"
            >
              <MessageSquare className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
