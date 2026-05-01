"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useChats, useCreateChat } from "@/entities/chat/api/chat-api";
import { ChatListItem } from "@/entities/chat/ui/chat-list-item";
import { useChatStore } from "@/entities/chat/model/chat-store";
import { Button } from "@/shared/ui/button";
import { Plus, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

export function Sidebar() {
  const router = useRouter();
  const { data: chats = [], isLoading } = useChats();
  const createChat = useCreateChat();
  const { activeChatId } = useChatStore();
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const handleNewChat = async () => {
    createChat.mutate(undefined, {
      onSuccess: (data) => {
        router.push(`/chat/${data.id}`);
      },
    });
  };

  return (
    <div className="flex h-screen w-64 shrink-0 flex-col bg-[var(--bg-sidebar)] border-r border-[var(--border)]">
      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={handleNewChat}
          disabled={createChat.isPending}
          className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium text-[var(--text-primary)] transition-colors hover:bg-black/5 disabled:opacity-50 dark:hover:bg-white/5"
        >
          <Plus className="h-4 w-4 shrink-0" />
          Новый чат
        </button>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {isLoading ? (
          <div className="space-y-1 px-1">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-9 rounded-xl bg-black/5 animate-pulse dark:bg-white/5"
              />
            ))}
          </div>
        ) : chats.length === 0 ? (
          <div className="px-3 py-6 text-center text-xs text-[var(--text-muted)]">
            Нет чатов
          </div>
        ) : (
          <div className="space-y-0.5">
            {chats.map((chat) => (
              <ChatListItem
                key={chat.id}
                chat={chat}
                isActive={activeChatId === chat.id}
              />
            ))}
          </div>
        )}
      </div>

      {/* Theme Toggle */}
      <div className="border-t border-[var(--border)] p-3">
        <button
          onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
          className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm text-[var(--text-secondary)] transition-colors hover:bg-black/5 dark:hover:bg-white/5"
        >
          {mounted && resolvedTheme === "dark" ? (
            <>
              <Sun className="h-4 w-4 shrink-0" />
              Светлая тема
            </>
          ) : (
            <>
              <Moon className="h-4 w-4 shrink-0" />
              Тёмная тема
            </>
          )}
        </button>
      </div>
    </div>
  );
}
