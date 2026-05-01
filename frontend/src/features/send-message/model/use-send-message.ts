"use client";

/**
 * Hook for sending messages with streaming
 */

import { useMessageStore } from "@/entities/message/model/message-store";
import { readSSEStream } from "@/shared/lib/streaming";
import { SSEEvent, Message } from "@/entities/message/model/types";
import { useQueryClient } from "@tanstack/react-query";

export function useSendMessage(chatId: string) {
  const queryClient = useQueryClient();
  const {
    addMessage,
    setIsStreaming,
    setStreamingMessageId,
    appendStreamingContent,
    resetStreaming,
  } = useMessageStore();

  return async (content: string) => {
    if (!content.trim() || !chatId) return;

    // Add user message optimistically
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      chat_id: chatId,
      role: "user",
      content,
      created_at: new Date().toISOString(),
      is_summarized: false,
    };
    addMessage(userMessage);

    // Create placeholder for assistant message
    const placeholderId = `streaming-${Date.now()}`;
    const placeholderMessage: Message = {
      id: placeholderId,
      chat_id: chatId,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
      is_summarized: false,
    };
    addMessage(placeholderMessage);

    // Start streaming
    setIsStreaming(true);
    setStreamingMessageId(placeholderId);

    try {
      const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/chats/${chatId}/messages`;

      let pendingChunk = "";
      let rafId: number | null = null;

      const flush = () => {
        if (pendingChunk) {
          appendStreamingContent(pendingChunk);
          pendingChunk = "";
        }
        rafId = null;
      };

      for await (const event of readSSEStream(url, { content })) {
        if (event.type === "delta" && event.content) {
          pendingChunk += event.content;
          if (!rafId) rafId = requestAnimationFrame(flush);
        } else if (event.type === "done") {
          if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
          flush();
          // Replace placeholder with real message
          const finalMessage: Message = {
            id: event.message_id || placeholderId,
            chat_id: chatId,
            role: "assistant",
            content: event.content || "",
            created_at: new Date().toISOString(),
            is_summarized: false,
          };

          // Update the placeholder message
          const { messages } = useMessageStore.getState();
          const messageIndex = messages.findIndex((m) => m.id === placeholderId);
          if (messageIndex !== -1) {
            messages[messageIndex] = finalMessage;
            useMessageStore.setState({ messages: [...messages] });
          }

          // Refresh messages from server
          queryClient.invalidateQueries({ queryKey: ["chats", chatId, "messages"] });
          // Refresh chat list once immediately, then again after title generation delay
          queryClient.invalidateQueries({ queryKey: ["chats"] });
          setTimeout(() => queryClient.invalidateQueries({ queryKey: ["chats"] }), 3000);
          setTimeout(() => queryClient.invalidateQueries({ queryKey: ["chats"] }), 6000);
        } else if (event.type === "error") {
          console.error("Stream error:", event.detail);
        }
      }
    } catch (error) {
      console.error("Failed to stream message:", error);
    } finally {
      resetStreaming();
    }
  };
}
