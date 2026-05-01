"use client";

/**
 * Markdown renderer with syntax highlighting
 */

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { type ComponentPropsWithoutRef } from "react";

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Custom link styling
          a: ({ href, children }) => (
            <a
              href={href}
              className="text-blue-500 hover:underline dark:text-blue-400"
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
          // Code block styling
          pre: ({ children }) => (
            <pre className="my-3 overflow-x-auto rounded-xl border border-[var(--border)] bg-[#f0f0f0] p-4 dark:bg-[#1e1e2e]">
              {children}
            </pre>
          ),
          code: ({ children, className, ...props }: ComponentPropsWithoutRef<"code">) => {
            const isInline = !className?.includes("language-");
            if (isInline) {
              return (
                <code
                  className="rounded-md bg-[#e4e4e4] px-1.5 py-0.5 font-mono text-[0.82em] text-[#c7254e] dark:bg-[#2a2a3d] dark:text-[#e06c75]"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code
                className="font-mono text-sm leading-relaxed text-[#1a1a1a] dark:text-[#cdd6f4]"
                {...props}
              >
                {children}
              </code>
            );
          },
          // List styling
          ul: ({ children }) => (
            <ul className="list-inside list-disc space-y-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-inside list-decimal space-y-1">{children}</ol>
          ),
          // Heading styling
          h1: ({ children }) => (
            <h1 className="mb-2 text-xl font-bold">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="mb-2 text-lg font-bold">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="mb-2 font-bold">{children}</h3>
          ),
          // Quote styling
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-gray-300 pl-4 italic dark:border-gray-700">
              {children}
            </blockquote>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
