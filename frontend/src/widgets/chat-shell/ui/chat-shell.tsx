"use client";

import { ReactNode, useState } from "react";
import { Menu, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { Sidebar } from "@/widgets/sidebar/ui/sidebar";

interface ChatShellProps {
  children: ReactNode;
}

export function ChatShell({ children }: ChatShellProps) {
  const [isDesktopSidebarOpen, setIsDesktopSidebarOpen] = useState(true);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-white dark:bg-gray-950">
      {isMobileSidebarOpen ? (
        <div
          className="fixed inset-0 z-40 bg-black/40 transition-opacity duration-200 md:hidden"
          onClick={() => setIsMobileSidebarOpen(false)}
        />
      ) : null}

      <Sidebar
        isDesktopOpen={isDesktopSidebarOpen}
        isMobileOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <div className="flex h-14 shrink-0 items-center gap-2 border-b border-[var(--border)] bg-[var(--bg-secondary)] px-3 sm:px-4">
          <button
            type="button"
            onClick={() => setIsMobileSidebarOpen(true)}
            className="flex h-9 w-9 items-center justify-center rounded-xl text-[var(--text-secondary)] transition-colors hover:bg-black/5 dark:hover:bg-white/5 md:hidden"
            aria-label="Открыть список чатов"
          >
            <Menu className="h-4 w-4" />
          </button>

          <button
            type="button"
            onClick={() => setIsDesktopSidebarOpen((current) => !current)}
            className="hidden items-center gap-2 rounded-xl px-3 py-2 text-sm text-[var(--text-secondary)] transition-colors hover:bg-black/5 dark:hover:bg-white/5 md:flex"
            aria-label={
              isDesktopSidebarOpen
                ? "Скрыть список чатов"
                : "Показать список чатов"
            }
          >
            {isDesktopSidebarOpen ? (
              <PanelLeftClose className="h-4 w-4" />
            ) : (
              <PanelLeftOpen className="h-4 w-4" />
            )}
            <span>
              {isDesktopSidebarOpen ? "Скрыть список" : "Показать список"}
            </span>
          </button>
        </div>

        <div className="flex min-h-0 flex-1 overflow-hidden">{children}</div>
      </div>
    </div>
  );
}
