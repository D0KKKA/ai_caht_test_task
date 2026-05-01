/**
 * Chat API hooks and queries
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/shared/api/client";
import { Chat, CreateChatRequest } from "../model/types";

/**
 * Get all chats for the user
 */
export function useChats() {
  return useQuery({
    queryKey: ["chats"],
    queryFn: async () => {
      const response = await apiClient.get<Chat[]>("/chats");
      return response.data;
    },
    refetchOnWindowFocus: false,
  });
}

/**
 * Get single chat by ID
 * Includes title polling: refetches every 2s until title is set
 */
export function useChat(chatId: string) {
  return useQuery({
    queryKey: ["chats", chatId],
    queryFn: async () => {
      const response = await apiClient.get<Chat>(`/chats/${chatId}`);
      return response.data;
    },
    enabled: !!chatId,
    // Poll for title if not set
    refetchInterval: (query) => {
      return query.state.data?.title ? false : 2000; // Stop polling once title is set
    },
  });
}

/**
 * Create new chat
 */
export function useCreateChat() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post<Chat>("/chats", {});
      return response.data;
    },
    onSuccess: (newChat) => {
      // Invalidate chats list to refetch
      queryClient.invalidateQueries({ queryKey: ["chats"] });
    },
  });
}

/**
 * Delete chat
 */
export function useDeleteChat() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (chatId: string) => {
      await apiClient.delete(`/chats/${chatId}`);
    },
    onSuccess: () => {
      // Invalidate chats list
      queryClient.invalidateQueries({ queryKey: ["chats"] });
    },
  });
}
