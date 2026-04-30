"use client";

import { Sidebar } from "@/widgets/sidebar/ui/sidebar";
import { ChatArea } from "@/widgets/chat-area/ui/chat-area";
import { useChatStore } from "@/entities/chat/model/chat-store";
import { useParams } from "next/navigation";
import { useEffect } from "react";

export const dynamic = "force-dynamic";

export default function ChatPage() {
  const params = useParams();
  const chatId = params?.id as string;
  const { setActiveChatId } = useChatStore();

  useEffect(() => {
    if (chatId) setActiveChatId(chatId);
  }, [chatId, setActiveChatId]);

  return (
    <div className="flex h-screen bg-white dark:bg-gray-950">
      <Sidebar />
      <ChatArea chatId={chatId} />
    </div>
  );
}
