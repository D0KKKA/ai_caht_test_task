export interface Chat {
  id: string;
  client_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}
