"use client";

import { useCallback } from "react";
import { API_BASE_PATH } from "@/shared/lib/api";
import { useMessageStreamExecutor } from "./use-message-stream-executor";

export function useRegenerateMessage(chatId: string) {
  const executeStream = useMessageStreamExecutor(chatId);

  return useCallback(
    async (messageId: string, previousContent: string) => {
      if (!chatId || !messageId) {
        return;
      }

      await executeStream({
        endpoint: `${API_BASE_PATH}/chats/${chatId}/messages/regenerate`,
        body: {},
        assistantMessageId: messageId,
        prepareOptimisticState: (current) =>
          current.map((message) =>
            message.id === messageId ? { ...message, content: "" } : message,
          ),
        rollbackState: (current) =>
          current.map((message) =>
            message.id === messageId
              ? { ...message, content: previousContent }
              : message,
          ),
        finalizeState: (current, event, finalContent) =>
          current.map((message) =>
            message.id === messageId
              ? {
                  ...message,
                  id: event.message_id || messageId,
                  content: finalContent,
                }
              : message,
          ),
      });
    },
    [chatId, executeStream],
  );
}
