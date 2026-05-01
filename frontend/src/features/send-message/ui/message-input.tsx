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

  // Refocus textarea after streaming ends
  useEffect(() => {
    if (!isStreaming) {
      textareaRef.current?.focus();
    }
  }, [isStreaming]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() || isStreaming) return;
    if (onSendMessage) {
      await onSendMessage(content);
    } else {
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
    <form onSubmit={handleSubmit} className="flex items-center gap-3 rounded-2xl border border-[var(--border-strong)] bg-[var(--bg-secondary)] px-4 py-2.5 shadow-[var(--shadow-md)] transition-all focus-within:border-[var(--accent)] focus-within:shadow-[0_0_0_3px_rgba(16,163,127,0.12),var(--shadow-md)]">
      <textarea
        ref={textareaRef}
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled || isStreaming}
        placeholder="Напишите сообщение…"
        className="flex-1 resize-none bg-transparent py-1 text-sm leading-6 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none disabled:opacity-50"
        rows={1}
        style={{ maxHeight: "200px" }}
      />
      <button
        type="submit"
        disabled={isDisabled}
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-white transition-opacity disabled:opacity-30 hover:bg-[var(--accent-hover)]"
      >
        <Send className="h-3.5 w-3.5" />
      </button>
    </form>
  );
}
