"use client";

import { useEffect, useRef } from "react";
import { Message } from "../model/types";
import { MessageBubble } from "./message-bubble";
import { StreamingCursor } from "./streaming-cursor";

interface MessageFeedProps {
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
}

export function MessageFeed({
  messages,
  isStreaming,
  streamingContent,
}: MessageFeedProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      if (scrollContainerRef.current) {
        scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
      }
    });
    return () => cancelAnimationFrame(raf);
  }, [messages, isStreaming, streamingContent]);

  return (
    <div
      ref={scrollContainerRef}
      className="flex-1 overflow-y-auto"
    >
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
              <MessageBubble key={message.id} message={message} />
            ))}
            {isStreaming && (
              <div className="flex justify-start">
                <div className="w-full text-sm leading-relaxed text-[var(--text-primary)]">
                  <span className="whitespace-pre-wrap break-words">{streamingContent}</span>
                  <StreamingCursor />
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
