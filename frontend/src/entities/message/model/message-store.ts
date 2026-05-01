import { create } from "zustand";

interface MessageStore {
  isStreaming: boolean;
  streamingChatId: string | null;
  streamingMessageId: string | null;

  startStreaming: (chatId: string, messageId: string) => void;
  finishStreaming: () => void;
}

export const useMessageStore = create<MessageStore>((set) => ({
  isStreaming: false,
  streamingChatId: null,
  streamingMessageId: null,

  startStreaming: (chatId, messageId) =>
    set({
      isStreaming: true,
      streamingChatId: chatId,
      streamingMessageId: messageId,
    }),

  finishStreaming: () =>
    set({
      isStreaming: false,
      streamingChatId: null,
      streamingMessageId: null,
    }),
}));
