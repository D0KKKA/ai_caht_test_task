/**
 * Message API hooks and queries
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/shared/api/client";
import { Message } from "../model/types";

/**
 * Get all messages for a chat
 */
export function useMessages(chatId: string) {
  return useQuery({
    queryKey: ["chats", chatId, "messages"],
    queryFn: async () => {
      console.log("[useMessages] Fetching messages for chat:", chatId);
      try {
        const response = await apiClient.get<Message[]>(
          `/chats/${chatId}/messages`
        );
        console.log("[useMessages] Success:", response.data);
        return response.data;
      } catch (error) {
        console.error("[useMessages] Error:", error);
        throw error;
      }
    },
    enabled: !!chatId,
  });
}
