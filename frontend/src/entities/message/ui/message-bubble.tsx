"use client";

import { useState } from "react";
import { Message } from "../model/types";
import { MarkdownRenderer } from "@/shared/ui/markdown-renderer";
import { Copy, Check } from "lucide-react";
import { StreamingCursor } from "./streaming-cursor";

interface MessageBubbleProps {
  message: Message;
  showStreamingCursor?: boolean;
}

export function MessageBubble({
  message,
  showStreamingCursor = false,
}: MessageBubbleProps) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      {isUser ? (
        <div className="max-w-[70%] rounded-2xl bg-[var(--user-msg-bg)] px-4 py-3 text-[var(--text-primary)] ring-1 ring-[var(--border)]">
          <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">{message.content}</p>
        </div>
      ) : (
        <div className="group w-full py-1">
          <div className="prose prose-sm max-w-none text-[var(--text-primary)] leading-relaxed
            prose-p:my-1.5 prose-p:leading-relaxed
            prose-headings:text-[var(--text-primary)] prose-headings:font-semibold
            prose-code:text-[var(--text-primary)] prose-code:bg-[var(--bg-secondary)] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
            prose-pre:bg-[var(--bg-secondary)] prose-pre:border prose-pre:border-[var(--border)] prose-pre:rounded-xl
            prose-a:text-[var(--accent)] prose-a:no-underline hover:prose-a:underline
            prose-strong:text-[var(--text-primary)] prose-strong:font-semibold
            prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5">
            <MarkdownRenderer content={message.content} />
            {showStreamingCursor ? (
              <div className="mt-2 flex text-[var(--text-primary)]">
                <StreamingCursor />
              </div>
            ) : null}
          </div>
          <div className="mt-1 flex opacity-0 transition-opacity group-hover:opacity-100">
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs text-[var(--text-muted)] transition-colors hover:bg-[var(--bg-primary)] hover:text-[var(--text-secondary)]"
            >
              {copied ? (
                <>
                  <Check className="h-3.5 w-3.5 text-[var(--accent)]" />
                  <span className="text-[var(--accent)]">Скопировано</span>
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" />
                  <span>Копировать</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
