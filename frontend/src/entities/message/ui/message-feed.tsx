"use client";

import { useEffect, useRef } from "react";
import { Message } from "../model/types";
import { MessageBubble } from "./message-bubble";

interface MessageFeedProps {
  messages: Message[];
  isStreaming: boolean;
  streamingMessageId: string | null;
  regeneratableMessageId?: string | null;
  onRegenerateMessage?: (message: Message) => Promise<void> | void;
}

export function MessageFeed({
  messages,
  isStreaming,
  streamingMessageId,
  regeneratableMessageId = null,
  onRegenerateMessage,
}: MessageFeedProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      if (scrollContainerRef.current) {
        scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
      }
    });
    return () => cancelAnimationFrame(raf);
  }, [messages, isStreaming]);

  return (
    <div ref={scrollContainerRef} className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto max-w-3xl px-6 py-8">
        {messages.length === 0 && !isStreaming ? (
          <div className="flex h-[60vh] items-center justify-center">
            <div className="text-center">
              <div className="mb-4 text-4xl">✦</div>
              <p className="text-lg font-medium text-[var(--text-primary)]">Чем могу помочь?</p>
              <p className="mt-1 text-sm text-[var(--text-muted)]">Напишите сообщение, чтобы начать разговор</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                showStreamingCursor={
                  isStreaming && streamingMessageId === message.id
                }
                showRegenerate={regeneratableMessageId === message.id}
                onRegenerate={onRegenerateMessage}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
