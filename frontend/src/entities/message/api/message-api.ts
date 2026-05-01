import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/shared/api/client";
import { Message } from "../model/types";

export function useMessages(chatId: string) {
  return useQuery({
    queryKey: ["chats", chatId, "messages"],
    queryFn: async ({ signal }) => {
      const response = await apiClient.get<Message[]>(
        `/chats/${chatId}/messages`,
        { signal }
      );
      return response.data;
    },
    enabled: !!chatId,
  });
}
