"use client";

import { useEffect } from "react";
import { MessageFeed } from "@/entities/message/ui/message-feed";
import { MessageInput } from "@/features/send-message/ui/message-input";
import { useMessages } from "@/entities/message/api/message-api";
import { useMessageStore } from "@/entities/message/model/message-store";
import { useSendMessage } from "@/features/send-message/model/use-send-message";

interface ChatAreaProps {
  chatId: string;
}

export function ChatArea({ chatId }: ChatAreaProps) {
  const { data: serverMessages = [] } = useMessages(chatId);
  const { messages: localMessages, isStreaming, streamingContent, clearMessages, resetStreaming } = useMessageStore();
  const sendMessage = useSendMessage(chatId);

  // Сбрасываем локальные сообщения при смене чата
  useEffect(() => {
    clearMessages();
    resetStreaming();
  }, [chatId]);

  // Когда сервер вернул сообщения после стриминга — убираем оптимистичные дубликаты
  useEffect(() => {
    if (!isStreaming && serverMessages.length > 0 && localMessages.length > 0) {
      clearMessages();
    }
  }, [serverMessages.length, isStreaming]);

  // Auto-send pending message from new chat creation
  useEffect(() => {
    if (typeof window !== "undefined") {
      const pending = sessionStorage.getItem("pendingMessage");
      if (pending) {
        sessionStorage.removeItem("pendingMessage");
        sendMessage(pending);
      }
    }
  }, [chatId, sendMessage]);

  // Во время стриминга показываем оптимистичные сообщения + серверные
  // После завершения — только серверные (localMessages уже очищены)
  const seen = new Set<string>();
  const displayMessages = (isStreaming
    ? [...serverMessages, ...localMessages]
    : serverMessages
  ).filter((msg) => {
    if (seen.has(msg.id)) return false;
    seen.add(msg.id);
    return true;
  });

  return (
    <div className="flex flex-1 flex-col bg-[var(--bg-secondary)]">
      <MessageFeed
        messages={displayMessages}
        isStreaming={isStreaming}
        streamingContent={streamingContent}
      />
      <div className="pb-6 pt-2">
        <div className="mx-auto max-w-3xl px-6">
          <MessageInput chatId={chatId} disabled={isStreaming} />
          <p className="mt-2 text-center text-xs text-[var(--text-muted)]">
            ИИ может ошибаться. Проверяйте важную информацию.
          </p>
        </div>
      </div>
    </div>
  );
}
