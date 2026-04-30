/**
 * Chat domain types
 */

export interface Chat {
  id: string;
  client_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface CreateChatRequest {
  // Empty - client_id comes from header
}

export interface UpdateChatRequest {
  title?: string;
}
