"use client";

import { usePathname, useRouter } from "next/navigation";
import { useChats } from "@/entities/chat/api/chat-api";
import { ChatListItem } from "@/entities/chat/ui/chat-list-item";
import { Moon, Plus } from "lucide-react";
import { useTheme } from "next-themes";

export function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const { data: chats = [], isLoading } = useChats();
  const { resolvedTheme, setTheme } = useTheme();

  const activeChatId = pathname.startsWith("/chat/")
    ? pathname.replace("/chat/", "")
    : null;

  const handleNewChat = () => {
    router.push("/chat");
  };

  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col overflow-hidden border-r border-[var(--border)] bg-[var(--bg-sidebar)]">
      <div className="p-3">
        <button
          type="button"
          onClick={handleNewChat}
          className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium text-[var(--text-primary)] transition-colors hover:bg-black/5 dark:hover:bg-white/5"
        >
          <Plus className="h-4 w-4 shrink-0" />
          Новый чат
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-2">
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

      <div className="border-t border-[var(--border)] p-3">
        <button
          type="button"
          onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
          className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm text-[var(--text-secondary)] transition-colors hover:bg-black/5 dark:hover:bg-white/5"
        >
          <Moon className="h-4 w-4 shrink-0" />
          Сменить тему
        </button>
      </div>
    </aside>
  );
}
