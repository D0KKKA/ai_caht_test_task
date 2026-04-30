"use client";

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

  const handleNewChat = async () => {
    createChat.mutate(undefined, {
      onSuccess: (data) => {
        router.push(`/chat/${data.id}`);
      },
    });
  };

  return (
    <div className="flex h-screen w-64 flex-col border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950">
      {/* Header */}
      <div className="border-b border-gray-200 p-4 dark:border-gray-800">
        <Button
          onClick={handleNewChat}
          className="w-full"
          disabled={createChat.isPending}
        >
          <Plus className="mr-2 h-4 w-4" />
          New Chat
        </Button>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="h-10 rounded-lg bg-gray-100 animate-pulse dark:bg-gray-800"
              />
            ))}
          </div>
        ) : chats.length === 0 ? (
          <div className="text-center text-sm text-gray-400 py-8">
            No chats yet
          </div>
        ) : (
          <div className="space-y-1">
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
      <div className="border-t border-gray-200 p-4 dark:border-gray-800">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
          className="w-full"
        >
          {resolvedTheme === "dark" ? (
            <>
              <Sun className="mr-2 h-4 w-4" />
              Light
            </>
          ) : (
            <>
              <Moon className="mr-2 h-4 w-4" />
              Dark
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
