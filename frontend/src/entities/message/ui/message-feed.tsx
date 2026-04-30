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
    if (scrollContainerRef.current) {
      const scrollContainer = scrollContainerRef.current;
      scrollContainer.scrollTop = scrollContainer.scrollHeight;
    }
  }, [messages, isStreaming, streamingContent]);

  return (
    <div
      ref={scrollContainerRef}
      className="flex-1 overflow-y-auto space-y-4 p-4"
    >
      {messages.length === 0 && !isStreaming ? (
        <div className="flex h-full items-center justify-center text-gray-400">
          <div className="text-center">
            <p className="text-lg">No messages yet</p>
            <p className="text-sm">Send a message to start the conversation</p>
          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isStreaming && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg bg-gray-100 px-4 py-3 dark:bg-gray-800">
                <div className="whitespace-pre-wrap break-words text-gray-900 dark:text-gray-100">
                  {streamingContent}
                  <StreamingCursor />
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
