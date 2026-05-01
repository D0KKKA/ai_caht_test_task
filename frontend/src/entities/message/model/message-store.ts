import { create } from "zustand";

interface StreamingSession {
  requestId: string;
  chatId: string;
  messageId: string;
  controller: AbortController;
}

interface MessageStore {
  isStreaming: boolean;
  streamingChatId: string | null;
  streamingMessageId: string | null;
  activeRequestId: string | null;
  abortController: AbortController | null;

  startStreaming: (session: StreamingSession) => void;
  finishStreaming: (requestId: string) => void;
  cancelStreaming: (requestId?: string) => void;
  cancelStreamingForChat: (chatId: string) => void;
}

const idleStreamingState = {
  isStreaming: false,
  streamingChatId: null,
  streamingMessageId: null,
  activeRequestId: null,
  abortController: null,
};

export const useMessageStore = create<MessageStore>((set, get) => ({
  ...idleStreamingState,

  startStreaming: ({ requestId, chatId, messageId, controller }) => {
    get().abortController?.abort();

    set({
      isStreaming: true,
      streamingChatId: chatId,
      streamingMessageId: messageId,
      activeRequestId: requestId,
      abortController: controller,
    });
  },

  finishStreaming: (requestId) => {
    if (get().activeRequestId !== requestId) {
      return;
    }

    set({ ...idleStreamingState });
  },

  cancelStreaming: (requestId) => {
    const { abortController, activeRequestId } = get();
    if (!abortController || (requestId && activeRequestId !== requestId)) {
      return;
    }

    abortController.abort();
    set({ ...idleStreamingState });
  },

  cancelStreamingForChat: (chatId) => {
    const { abortController, streamingChatId } = get();
    if (!abortController || streamingChatId !== chatId) {
      return;
    }

    abortController.abort();
    set({ ...idleStreamingState });
  },
}));
