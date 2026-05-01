import { SSEEvent } from "@/entities/message/model/types";
import { getOrCreateClientId } from "@/shared/lib/client-id";

interface ReadSSEStreamOptions {
  signal?: AbortSignal;
}

export async function* readSSEStream(
  url: string,
  body: Record<string, unknown>,
  options: ReadSSEStreamOptions = {}
): AsyncGenerator<SSEEvent> {
  const clientId = getOrCreateClientId();

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(clientId ? { "X-Client-Id": clientId } : {}),
    },
    body: JSON.stringify(body),
    cache: "no-store",
    signal: options.signal,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }

  if (!response.body) {
    throw new Error("Streaming response body is empty");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const cancelReader = () => {
    void reader.cancel().catch(() => undefined);
  };

  options.signal?.addEventListener("abort", cancelReader);

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const normalizedBuffer = buffer.replace(/\r\n/g, "\n");
      const chunks = normalizedBuffer.split("\n\n");
      buffer = chunks.pop() || "";

      for (const chunk of chunks) {
        const event = parseSSEEvent(chunk);
        if (event) {
          yield event;
        }
      }
    }

    if (buffer.trim()) {
      const event = parseSSEEvent(buffer);
      if (event) {
        yield event;
      }
    }
  } finally {
    options.signal?.removeEventListener("abort", cancelReader);
    reader.releaseLock();
  }
}

export function isAbortError(error: unknown): boolean {
  return (
    error instanceof DOMException
      ? error.name === "AbortError"
      : error instanceof Error && error.name === "AbortError"
  );
}

function parseSSEEvent(chunk: string): SSEEvent | null {
  const dataLine = chunk
    .split("\n")
    .find((line) => line.startsWith("data:"));

  if (!dataLine) {
    return null;
  }

  try {
    return JSON.parse(dataLine.slice(5).trim()) as SSEEvent;
  } catch {
    return null;
  }
}
