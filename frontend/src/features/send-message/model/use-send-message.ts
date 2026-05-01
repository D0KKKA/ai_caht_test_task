"use client";

import { useCallback } from "react";
import { Message } from "@/entities/message/model/types";
import { API_BASE_PATH } from "@/shared/lib/api";
import { useMessageStreamExecutor } from "./use-message-stream-executor";

export function useSendMessage(chatId: string) {
  const executeStream = useMessageStreamExecutor(chatId);

  return useCallback(
    async (rawContent: string) => {
      const content = rawContent.trim();

      if (!content || !chatId) {
        return;
      }

      const createdAt = new Date().toISOString();
      const userMessageId = `temp-user-${crypto.randomUUID()}`;
      const assistantMessageId = `temp-assistant-${crypto.randomUUID()}`;

      const userMessage: Message = {
        id: userMessageId,
        chat_id: chatId,
        role: "user",
        content,
        created_at: createdAt,
        is_summarized: false,
      };

      const assistantMessage: Message = {
        id: assistantMessageId,
        chat_id: chatId,
        role: "assistant",
        content: "",
        created_at: createdAt,
        is_summarized: false,
      };

      await executeStream({
        endpoint: `${API_BASE_PATH}/chats/${chatId}/messages`,
        body: {
          content,
        },
        assistantMessageId,
        prepareOptimisticState: (current) => [
          ...current,
          userMessage,
          assistantMessage,
        ],
        rollbackState: (current) =>
          current.filter((message) => message.id !== assistantMessageId),
        finalizeState: (current, event, finalContent) =>
          current.map((message) =>
            message.id === assistantMessageId
              ? {
                  ...message,
                  id: event.message_id || assistantMessageId,
                  content: finalContent,
                }
              : message,
          ),
      });
    },
    [chatId, executeStream],
  );
}
