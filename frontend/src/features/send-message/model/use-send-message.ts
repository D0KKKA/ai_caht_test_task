"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Message } from "@/entities/message/model/types";
import { useMessageStore } from "@/entities/message/model/message-store";
import { API_BASE_PATH } from "@/shared/lib/api";
import { readSSEStream } from "@/shared/lib/streaming";

export function useSendMessage(chatId: string) {
  const queryClient = useQueryClient();
  const { startStreaming, finishStreaming } = useMessageStore();

  return async (rawContent: string) => {
    const content = rawContent.trim();

    if (!content || !chatId) {
      return;
    }

    const queryKey = ["chats", chatId, "messages"] as const;
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

    await queryClient.cancelQueries({ queryKey });
    queryClient.setQueryData<Message[]>(queryKey, (current = []) => [
      ...current,
      userMessage,
      assistantMessage,
    ]);
    startStreaming(chatId, assistantMessageId);

    let pendingChunk = "";
    let rafId: number | null = null;
    let finalContent = "";

    const flushPendingChunk = () => {
      if (!pendingChunk) {
        rafId = null;
        return;
      }

      const chunk = pendingChunk;
      pendingChunk = "";
      finalContent += chunk;
      queryClient.setQueryData<Message[]>(queryKey, (current = []) =>
        current.map((message) =>
          message.id === assistantMessageId
            ? { ...message, content: message.content + chunk }
            : message
        )
      );
      rafId = null;
    };

    try {
      for await (const event of readSSEStream(
        `${API_BASE_PATH}/chats/${chatId}/messages`,
        { content }
      )) {
        if (event.type === "delta" && event.content) {
          pendingChunk += event.content;

          if (rafId === null) {
            rafId = requestAnimationFrame(flushPendingChunk);
          }

          continue;
        }

        if (event.type === "error") {
          throw new Error(event.detail || "Не удалось отправить сообщение.");
        }

        if (event.type === "done") {
          if (rafId !== null) {
            cancelAnimationFrame(rafId);
            rafId = null;
          }

          flushPendingChunk();
          if (!finalContent && event.content) {
            finalContent = event.content;
          }

          queryClient.setQueryData<Message[]>(queryKey, (current = []) =>
            current.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    id: event.message_id || assistantMessageId,
                    content: finalContent,
                  }
                : message
            )
          );

          queryClient.invalidateQueries({ queryKey });
          queryClient.invalidateQueries({ queryKey: ["chats"] });
          return;
        }
      }

      throw new Error("Поток ответа завершился неожиданно.");
    } catch (error) {
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }

      queryClient.setQueryData<Message[]>(queryKey, (current = []) =>
        current.filter((message) => message.id !== assistantMessageId)
      );
      queryClient.invalidateQueries({ queryKey });
      throw error;
    } finally {
      finishStreaming();
    }
  };
}
