"use client";

import { Chat } from "../model/types";
import { Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useDeleteChat } from "../api/chat-api";

interface ChatListItemProps {
  chat: Chat;
  isActive: boolean;
  onSelect?: () => void;
}

export function ChatListItem({ chat, isActive, onSelect }: ChatListItemProps) {
  const router = useRouter();
  const deleteChat = useDeleteChat();

  const handleClick = () => {
    router.push(`/chat/${chat.id}`);
    onSelect?.();
  };

  const handleDelete = () => {
    deleteChat.mutate(chat.id, {
      onSuccess: () => {
        if (isActive) {
          router.replace("/chat");
          onSelect?.();
        }
      },
    });
  };

  return (
    <div
      className={`group flex items-center justify-between rounded-xl px-3 py-2 text-sm transition-colors ${
        isActive
          ? "bg-black/10 font-medium text-[var(--text-primary)] dark:bg-white/10"
          : "text-[var(--text-secondary)] hover:bg-black/5 dark:hover:bg-white/5"
      }`}
    >
      <button
        type="button"
        onClick={handleClick}
        className="min-w-0 flex-1 truncate text-left leading-snug"
      >
        {chat.title || "Новый чат"}
      </button>
      <button
        type="button"
        onClick={handleDelete}
        disabled={deleteChat.isPending}
        className="ml-1 shrink-0 rounded-lg p-1 text-[var(--text-muted)] opacity-0 transition-opacity group-hover:opacity-100 hover:bg-red-100 hover:text-red-500 disabled:opacity-30 dark:hover:bg-red-900/30 dark:hover:text-red-400"
        aria-label="Удалить чат"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
