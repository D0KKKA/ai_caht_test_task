"use client";

import { Sidebar } from "@/widgets/sidebar/ui/sidebar";
import { MessageInput } from "@/features/send-message/ui/message-input";
import { useRouter } from "next/navigation";
import { useCreateChat } from "@/entities/chat/api/chat-api";

export default function NewChatPage() {
  const router = useRouter();
  const createChat = useCreateChat();

  const handleSendMessage = async (content: string) => {
    // Create chat and send first message
    createChat.mutate(undefined, {
      onSuccess: (data) => {
        // Navigate to the new chat - it will handle sending the message
        router.push(`/chat/${data.id}`);
        // Store the message to be sent in session storage
        sessionStorage.setItem("pendingMessage", content);
      },
    });
  };

  return (
    <div className="flex h-screen bg-white dark:bg-gray-950">
      <Sidebar />
      <div className="flex flex-1 flex-col items-center justify-center">
        <div className="w-full max-w-2xl space-y-8 px-4">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
              Welcome
            </h1>
            <p className="mt-2 text-gray-500 dark:text-gray-400">
              Send a message to start a new conversation
            </p>
          </div>
          <div className="w-full">
            <MessageInput
              chatId="new"
              onSendMessage={handleSendMessage}
              disabled={createChat.isPending}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
