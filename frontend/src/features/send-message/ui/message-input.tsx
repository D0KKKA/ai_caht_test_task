"use client";

/**
 * Message input component
 */

import { useState, useRef, useEffect } from "react";
import { Button } from "@/shared/ui/button";
import { useMessageStore } from "@/entities/message/model/message-store";
import { useSendMessage } from "../model/use-send-message";
import { Send } from "lucide-react";

interface MessageInputProps {
  chatId: string;
  disabled?: boolean;
  onSendMessage?: (content: string) => void | Promise<void>;
}

export function MessageInput({
  chatId,
  disabled = false,
  onSendMessage,
}: MessageInputProps) {
  const [content, setContent] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isStreaming = useMessageStore((s) => s.isStreaming);
  const sendMessage = useSendMessage(chatId);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [content]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log("[MessageInput] handleSubmit:", { content, isStreaming, chatId });

    if (!content.trim() || isStreaming) {
      console.log("[MessageInput] Skipped: empty or streaming");
      return;
    }

    console.log("[MessageInput] Calling sendMessage or onSendMessage");
    if (onSendMessage) {
      console.log("[MessageInput] Using custom onSendMessage");
      await onSendMessage(content);
    } else {
      console.log("[MessageInput] Using sendMessage");
      await sendMessage(content);
    }
    setContent("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter, newline on Shift+Enter
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const isDisabled = disabled || isStreaming || !content.trim();

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <textarea
        ref={textareaRef}
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled || isStreaming}
        placeholder="Send a message... (Shift+Enter for newline)"
        className="flex-1 resize-none rounded-lg border border-gray-200 p-3 dark:border-gray-700 dark:bg-gray-900 disabled:opacity-50"
        rows={1}
      />
      <Button
        type="submit"
        disabled={isDisabled}
        size="icon"
        className="h-10 w-10"
      >
        <Send className="h-4 w-4" />
      </Button>
    </form>
  );
}
