"use client";

import { useEffect, useRef } from "react";
import { EmptyChatState } from "@/shared/ui/empty-chat-state";
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
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-8">
        {messages.length === 0 && !isStreaming ? (
          <EmptyChatState />
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
