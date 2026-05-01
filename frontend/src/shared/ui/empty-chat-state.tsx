"use client";

import { cn } from "@/shared/lib/utils";

interface EmptyChatStateProps {
  className?: string;
}

export function EmptyChatState({ className }: EmptyChatStateProps) {
  return (
    <div className={cn("flex h-[60vh] items-center justify-center", className)}>
      <div className="text-center">
        <div className="mb-4 text-4xl">✦</div>
        <p className="text-lg font-medium text-[var(--text-primary)]">
          Чем могу помочь?
        </p>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Напишите сообщение, чтобы начать разговор
        </p>
      </div>
    </div>
  );
}
