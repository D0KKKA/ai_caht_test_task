"use client";

import { Sidebar } from "@/widgets/sidebar/ui/sidebar";
import { ChatArea } from "@/widgets/chat-area/ui/chat-area";
import { useChatStore } from "@/entities/chat/model/chat-store";
import { useEffect } from "react";

interface ChatPageProps {
  params: {
    id: string;
  };
}

export default function ChatPage({ params }: ChatPageProps) {
  const { setActiveChatId } = useChatStore();

  useEffect(() => {
    setActiveChatId(params.id);
  }, [params.id, setActiveChatId]);

  return (
    <div className="flex h-screen bg-white dark:bg-gray-950">
      <Sidebar />
      <ChatArea chatId={params.id} />
    </div>
  );
}
