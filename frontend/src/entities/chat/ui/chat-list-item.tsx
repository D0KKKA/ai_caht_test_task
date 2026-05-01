"use client";

import { Chat } from "../model/types";
import { Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useDeleteChat } from "../api/chat-api";
import { useChatStore } from "../model/chat-store";

interface ChatListItemProps {
  chat: Chat;
  isActive: boolean;
}

export function ChatListItem({ chat, isActive }: ChatListItemProps) {
  const router = useRouter();
  const { setActiveChatId } = useChatStore();
  const deleteChat = useDeleteChat();

  const handleClick = () => {
    setActiveChatId(chat.id);
    router.push(`/chat/${chat.id}`);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    deleteChat.mutate(chat.id, {
      onSuccess: () => {
        if (isActive) router.push("/chat");
      },
    });
  };

  return (
    <div
      onClick={handleClick}
      className={`group flex cursor-pointer items-center justify-between rounded-xl px-3 py-2 text-sm transition-colors ${
        isActive
          ? "bg-black/10 font-medium text-[var(--text-primary)] dark:bg-white/10"
          : "text-[var(--text-secondary)] hover:bg-black/5 dark:hover:bg-white/5"
      }`}
    >
      <span className="flex-1 truncate leading-snug">
        {chat.title || "Новый чат"}
      </span>
      <button
        onClick={handleDelete}
        disabled={deleteChat.isPending}
        className="ml-1 shrink-0 rounded-lg p-1 opacity-0 text-[var(--text-muted)] transition-opacity group-hover:opacity-100 hover:bg-red-100 hover:text-red-500 disabled:opacity-30 dark:hover:bg-red-900/30 dark:hover:text-red-400"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
