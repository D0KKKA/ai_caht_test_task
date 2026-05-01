/**
 * Message domain types
 */

export interface Message {
  id: string;
  chat_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  is_summarized: boolean;
}

export interface SSEEvent {
  type: "delta" | "done" | "error";
  content?: string;
  message_id?: string;
  detail?: string;
}
