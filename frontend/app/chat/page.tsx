"use client";

import { useRouter } from "next/navigation";
import { useCreateChat } from "@/entities/chat/api/chat-api";
import { MessageInput } from "@/features/send-message/ui/message-input";
import { getPendingMessageStorageKey } from "@/shared/lib/pending-message";
import { Sidebar } from "@/widgets/sidebar/ui/sidebar";

export default function NewChatPage() {
  const router = useRouter();
  const createChat = useCreateChat();

  const handleSendMessage = async (content: string) => {
    const chat = await createChat.mutateAsync();
    sessionStorage.setItem(getPendingMessageStorageKey(chat.id), content);
    router.replace(`/chat/${chat.id}`);
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
