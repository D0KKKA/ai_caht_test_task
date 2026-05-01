"use client";

import { useEffect, useEffectEvent, useRef } from "react";
import { toast } from "sonner";
import { MessageFeed } from "@/entities/message/ui/message-feed";
import { MessageInput } from "@/features/send-message/ui/message-input";
import { useMessages } from "@/entities/message/api/message-api";
import { useMessageStore } from "@/entities/message/model/message-store";
import { useSendMessage } from "@/features/send-message/model/use-send-message";
import { getPendingMessageStorageKey } from "@/shared/lib/pending-message";

interface ChatAreaProps {
  chatId: string;
}

export function ChatArea({ chatId }: ChatAreaProps) {
  const { data: messages = [] } = useMessages(chatId);
  const { isStreaming, streamingChatId, streamingMessageId } = useMessageStore();
  const sendMessage = useSendMessage(chatId);
  const attemptedPendingChatIds = useRef<Set<string>>(new Set());

  const attemptPendingMessage = useEffectEvent(
    async (currentChatId: string, pendingMessage: string, storageKey: string) => {
      try {
        await sendMessage(pendingMessage);
        sessionStorage.removeItem(storageKey);
      } catch {
        attemptedPendingChatIds.current.delete(currentChatId);
        toast.error(
          "Не удалось отправить первое сообщение. Оно сохранено для повторной попытки."
        );
      }
    }
  );

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    if (attemptedPendingChatIds.current.has(chatId)) {
      return;
    }

    const storageKey = getPendingMessageStorageKey(chatId);
    const pendingMessage = sessionStorage.getItem(storageKey);

    if (!pendingMessage) {
      return;
    }

    attemptedPendingChatIds.current.add(chatId);
    void attemptPendingMessage(chatId, pendingMessage, storageKey);
  }, [chatId]);

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[var(--bg-secondary)]">
      <MessageFeed
        messages={messages}
        isStreaming={isStreaming && streamingChatId === chatId}
        streamingMessageId={streamingMessageId}
      />
      <div className="shrink-0 pb-6 pt-2">
        <div className="mx-auto max-w-3xl px-6">
          <MessageInput
            chatId={chatId}
            disabled={isStreaming && streamingChatId === chatId}
          />
          <p className="mt-2 text-center text-xs text-[var(--text-muted)]">
            ИИ может ошибаться. Проверяйте важную информацию.
          </p>
        </div>
      </div>
    </div>
  );
}
