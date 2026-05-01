"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Message, SSEEvent } from "@/entities/message/model/types";
import { useMessageStore } from "@/entities/message/model/message-store";
import { isAbortError, readSSEStream } from "@/shared/lib/streaming";

interface StreamExecutionOptions {
  endpoint: string;
  body: Record<string, unknown>;
  assistantMessageId: string;
  prepareOptimisticState: (current: Message[]) => Message[];
  rollbackState: (current: Message[]) => Message[];
  finalizeState: (
    current: Message[],
    event: SSEEvent,
    finalContent: string,
  ) => Message[];
}

export function useMessageStreamExecutor(chatId: string) {
  const queryClient = useQueryClient();
  const { startStreaming, finishStreaming } = useMessageStore();

  return async ({
    endpoint,
    body,
    assistantMessageId,
    prepareOptimisticState,
    rollbackState,
    finalizeState,
  }: StreamExecutionOptions) => {
    const queryKey = ["chats", chatId, "messages"] as const;
    const requestId = crypto.randomUUID();
    const controller = new AbortController();

    await queryClient.cancelQueries({ queryKey });
    queryClient.setQueryData<Message[]>(queryKey, (current = []) =>
      prepareOptimisticState(current),
    );

    startStreaming({
      requestId,
      chatId,
      messageId: assistantMessageId,
      controller,
    });

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
            : message,
        ),
      );
      rafId = null;
    };

    try {
      for await (const event of readSSEStream(endpoint, body, {
        signal: controller.signal,
      })) {
        if (event.type === "delta" && event.content) {
          pendingChunk += event.content;

          if (rafId === null) {
            rafId = requestAnimationFrame(flushPendingChunk);
          }

          continue;
        }

        if (event.type === "error") {
          throw new Error(event.detail || "Не удалось выполнить запрос.");
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
            finalizeState(current, event, finalContent),
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
        rollbackState(current),
      );
      queryClient.invalidateQueries({ queryKey });

      if (isAbortError(error)) {
        queryClient.invalidateQueries({ queryKey: ["chats"] });
        return;
      }

      throw error;
    } finally {
      finishStreaming(requestId);
    }
  };
}
