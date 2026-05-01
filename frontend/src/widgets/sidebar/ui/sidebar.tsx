"use client";

import { usePathname, useRouter } from "next/navigation";
import { useChats } from "@/entities/chat/api/chat-api";
import { ChatListItem } from "@/entities/chat/ui/chat-list-item";
import { Moon, Plus, X } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { useTheme } from "next-themes";

interface SidebarProps {
  isDesktopOpen: boolean;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
}

interface SidebarContentProps {
  activeChatId: string | null;
  onNavigate?: () => void;
}

function SidebarContent({ activeChatId, onNavigate }: SidebarContentProps) {
  const router = useRouter();
  const { data: chats = [], isLoading } = useChats();
  const { resolvedTheme, setTheme } = useTheme();

  const handleNewChat = () => {
    router.push("/chat");
    onNavigate?.();
  };

  return (
    <div className="flex h-full flex-col overflow-hidden bg-[var(--bg-sidebar)]">
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
                onSelect={onNavigate}
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
    </div>
  );
}

export function Sidebar({
  isDesktopOpen,
  isMobileOpen,
  onCloseMobile,
}: SidebarProps) {
  const pathname = usePathname();
  const activeChatId = pathname.startsWith("/chat/")
    ? pathname.replace("/chat/", "")
    : null;

  return (
    <>
      <aside
        className={cn(
          "hidden h-full shrink-0 overflow-hidden border-r border-[var(--border)] transition-[width] duration-200 md:flex",
          isDesktopOpen ? "w-64" : "w-0 border-r-0",
        )}
        aria-hidden={!isDesktopOpen}
      >
        <div
          className={cn(
            "flex w-64 min-w-64 flex-col overflow-hidden transition-opacity duration-200",
            isDesktopOpen ? "opacity-100" : "pointer-events-none opacity-0",
          )}
        >
          <SidebarContent activeChatId={activeChatId} />
        </div>
      </aside>

      {isMobileOpen ? (
        <aside className="fixed inset-y-0 left-0 z-50 flex w-[min(20rem,85vw)] flex-col overflow-hidden border-r border-[var(--border)] bg-[var(--bg-sidebar)] shadow-2xl transition-transform duration-200 md:hidden">
          <div className="flex items-center justify-between border-b border-[var(--border)] p-3">
            <span className="text-sm font-medium text-[var(--text-primary)]">
              Чаты
            </span>
            <button
              type="button"
              onClick={onCloseMobile}
              className="flex h-9 w-9 items-center justify-center rounded-xl text-[var(--text-secondary)] transition-colors hover:bg-black/5 dark:hover:bg-white/5"
              aria-label="Закрыть список чатов"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <SidebarContent
            activeChatId={activeChatId}
            onNavigate={onCloseMobile}
          />
        </aside>
      ) : null}
    </>
  );
}
