"use client";

import { useParams } from "next/navigation";
import { ChatArea } from "@/widgets/chat-area/ui/chat-area";

export default function ChatPage() {
  const params = useParams();
  const chatId = Array.isArray(params?.id) ? params.id[0] : params?.id;

  return <ChatArea key={chatId || "empty"} chatId={chatId || ""} />;
}
