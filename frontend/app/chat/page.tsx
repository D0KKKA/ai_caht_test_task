"use client";

import { useRouter } from "next/navigation";
import { useCreateChat } from "@/entities/chat/api/chat-api";
import { MessageInput } from "@/features/send-message/ui/message-input";
import { getPendingMessageStorageKey } from "@/shared/lib/pending-message";
import { EmptyChatState } from "@/shared/ui/empty-chat-state";

export default function NewChatPage() {
  const router = useRouter();
  const createChat = useCreateChat();

  const handleSendMessage = async (content: string) => {
    const chat = await createChat.mutateAsync();
    sessionStorage.setItem(getPendingMessageStorageKey(chat.id), content);
    router.replace(`/chat/${chat.id}`);
  };

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[var(--bg-secondary)]">
      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-8">
          <EmptyChatState />
        </div>
      </div>
      <div className="shrink-0 pb-6 pt-2">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <MessageInput
            chatId="new"
            onSendMessage={handleSendMessage}
            disabled={createChat.isPending}
          />
        </div>
      </div>
    </div>
  );
}
