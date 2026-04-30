/**
 * Server-Sent Events (SSE) stream parser
 */

import { SSEEvent } from "@/entities/message/model/types";

/**
 * Read SSE stream and yield events
 * Used for message streaming from backend
 */
export async function* readSSEStream(
  url: string,
  body: Record<string, unknown>
): AsyncGenerator<SSEEvent> {
  const clientId = getClientIdFromLocalStorage();
  console.log("[readSSEStream] Starting:", { url, clientId, bodyContent: body.content });

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Client-Id": clientId,
      },
      body: JSON.stringify(body),
    });

    console.log("[readSSEStream] Got response:", { status: response.status, ok: response.ok });

    if (!response.ok) {
      const text = await response.text();
      console.error("[readSSEStream] HTTP error:", { status: response.status, text });
      throw new Error(`HTTP error! status: ${response.status}: ${text}`);
    }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const event = JSON.parse(line.slice(6)) as SSEEvent;
            yield event;
          } catch (e) {
            console.error("Failed to parse SSE event:", e);
          }
        }
      }
    }

    // Process remaining buffer
    if (buffer.trim()) {
      if (buffer.startsWith("data: ")) {
        try {
          const event = JSON.parse(buffer.slice(6)) as SSEEvent;
          yield event;
        } catch (e) {
          console.error("Failed to parse final SSE event:", e);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
  } catch (error) {
    console.error("[readSSEStream] Error:", error);
    throw error;
  }
}

/**
 * Helper to get client ID from localStorage
 */
function getClientIdFromLocalStorage(): string {
  if (typeof window === "undefined") {
    return "";
  }
  return localStorage.getItem("client_id") || "";
}
