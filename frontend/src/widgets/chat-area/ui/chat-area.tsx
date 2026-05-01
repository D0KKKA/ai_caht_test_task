"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";
import { toast } from "sonner";
import { useMessages } from "@/entities/message/api/message-api";
import { useMessageStore } from "@/entities/message/model/message-store";
import { Message } from "@/entities/message/model/types";
import { MessageFeed } from "@/entities/message/ui/message-feed";
import { useRegenerateMessage } from "@/features/send-message/model/use-regenerate-message";
import { useSendMessage } from "@/features/send-message/model/use-send-message";
import { MessageInput } from "@/features/send-message/ui/message-input";
import { getPendingMessageStorageKey } from "@/shared/lib/pending-message";
import { getErrorMessage } from "@/shared/lib/error-message";

interface ChatAreaProps {
  chatId: string;
}

export function ChatArea({ chatId }: ChatAreaProps) {
  const { data: messages = [] } = useMessages(chatId);
  const {
    isStreaming,
    streamingChatId,
    streamingMessageId,
    cancelStreamingForChat,
  } = useMessageStore();
  const sendMessage = useSendMessage(chatId);
  const regenerateMessage = useRegenerateMessage(chatId);
  const attemptedPendingChatIds = useRef<Set<string>>(new Set());
  const isStreamingCurrentChat = isStreaming && streamingChatId === chatId;

  const regeneratableMessageId = useMemo(() => {
    const lastMessage = messages[messages.length - 1];

    if (!lastMessage || lastMessage.role !== "assistant" || isStreamingCurrentChat) {
      return null;
    }

    return lastMessage.id;
  }, [isStreamingCurrentChat, messages]);

  const attemptPendingMessage = useCallback(
    async (pendingMessage: string, storageKey: string) => {
      sessionStorage.removeItem(storageKey);

      try {
        await sendMessage(pendingMessage);
      } catch {
        sessionStorage.setItem(storageKey, pendingMessage);
        toast.error(
          "Не удалось отправить первое сообщение. Оно сохранено для повторной попытки.",
        );
      }
    },
    [sendMessage],
  );

  const handleRegenerateMessage = useCallback(
    async (message: Message) => {
      try {
        await regenerateMessage(message.id, message.content);
      } catch (error) {
        toast.error(getErrorMessage(error));
      }
    },
    [regenerateMessage],
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
    void attemptPendingMessage(pendingMessage, storageKey);
  }, [attemptPendingMessage, chatId]);

  useEffect(
    () => () => {
      cancelStreamingForChat(chatId);
    },
    [cancelStreamingForChat, chatId],
  );

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[var(--bg-secondary)]">
      <MessageFeed
        messages={messages}
        isStreaming={isStreamingCurrentChat}
        streamingMessageId={streamingMessageId}
        regeneratableMessageId={regeneratableMessageId}
        onRegenerateMessage={handleRegenerateMessage}
      />
      <div className="shrink-0 pb-6 pt-2">
        <div className="mx-auto max-w-3xl px-6">
          <MessageInput
            chatId={chatId}
            disabled={isStreamingCurrentChat}
          />
          <p className="mt-2 text-center text-xs text-[var(--text-muted)]">
            ИИ может ошибаться. Проверяйте важную информацию.
          </p>
        </div>
      </div>
    </div>
  );
}
