"use client";

import { useParams } from "next/navigation";
import { ChatArea } from "@/widgets/chat-area/ui/chat-area";
import { Sidebar } from "@/widgets/sidebar/ui/sidebar";

export default function ChatPage() {
  const params = useParams();
  const chatId = Array.isArray(params?.id) ? params.id[0] : params?.id;

  return (
    <div className="flex h-screen overflow-hidden bg-white dark:bg-gray-950">
      <Sidebar />
      <ChatArea key={chatId || "empty"} chatId={chatId || ""} />
    </div>
  );
}
