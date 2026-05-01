import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/shared/api/client";
import { Chat } from "../model/types";

export function useChats() {
  return useQuery({
    queryKey: ["chats"],
    queryFn: async () => {
      const response = await apiClient.get<Chat[]>("/chats");
      return response.data;
    },
    refetchOnWindowFocus: false,
    refetchInterval: (query) =>
      query.state.data?.some(
        (chat) => chat.title === null && chat.message_count > 0
      )
        ? 2000
        : false,
  });
}
export function useCreateChat() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post<Chat>("/chats", {});
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chats"] });
    },
  });
}
export function useDeleteChat() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (chatId: string) => {
      await apiClient.delete(`/chats/${chatId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chats"] });
    },
  });
}
