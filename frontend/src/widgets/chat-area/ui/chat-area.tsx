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
  const displayMessages = isStreaming
    ? [...serverMessages, ...localMessages]
    : serverMessages;

  return (
    <div className="flex flex-1 flex-col bg-white dark:bg-gray-950">
      <MessageFeed
        messages={displayMessages}
        isStreaming={isStreaming}
        streamingContent={streamingContent}
      />
      <div className="border-t border-gray-200 p-4 dark:border-gray-800">
        <MessageInput chatId={chatId} disabled={isStreaming} />
      </div>
    </div>
  );
}
