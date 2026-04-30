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
      className={`group flex cursor-pointer items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors ${
        isActive
          ? "bg-blue-500 text-white"
          : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
      }`}
    >
      <span className="flex-1 truncate">
        {chat.title || "Новый чат"}
      </span>
      <button
        onClick={handleDelete}
        disabled={deleteChat.isPending}
        className={`ml-2 shrink-0 rounded p-1 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-red-100 hover:text-red-600 disabled:opacity-30 dark:hover:bg-red-900/30 ${
          isActive ? "text-white hover:bg-blue-600 hover:text-white dark:hover:bg-blue-600" : ""
        }`}
      >
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
