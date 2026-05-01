"use client";

import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { useMessageStore } from "@/entities/message/model/message-store";
import { getErrorMessage } from "@/shared/lib/error-message";
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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isStreaming = useMessageStore(
    (state) => state.isStreaming && state.streamingChatId === chatId
  );
  const sendMessage = useSendMessage(chatId);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [content]);

  useEffect(() => {
    if (!isStreaming) {
      textareaRef.current?.focus();
    }
  }, [isStreaming]);

  const submitMessage = async () => {
    if (!content.trim() || isStreaming || isSubmitting) {
      return;
    }

    setIsSubmitting(true);

    try {
      if (onSendMessage) {
        await onSendMessage(content);
      } else {
        await sendMessage(content);
      }

      setContent("");
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    void submitMessage();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void submitMessage();
    }
  };

  const isDisabled = disabled || isStreaming || isSubmitting || !content.trim();

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-3 rounded-2xl border border-[var(--border-strong)] bg-[var(--bg-secondary)] px-4 py-2.5 shadow-[var(--shadow-md)] transition-all focus-within:border-[var(--accent)] focus-within:shadow-[0_0_0_3px_rgba(16,163,127,0.12),var(--shadow-md)]">
      <textarea
        ref={textareaRef}
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled || isStreaming || isSubmitting}
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
