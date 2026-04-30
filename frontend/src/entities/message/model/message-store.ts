/**
 * Message Zustand store for UI state
 */

import { create } from "zustand";
import { Message } from "./types";

interface MessageStore {
  // State
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  streamingMessageId: string | null;

  // Actions
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  clearMessages: () => void;

  // Streaming
  setIsStreaming: (value: boolean) => void;
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (chunk: string) => void;
  setStreamingMessageId: (id: string | null) => void;
  resetStreaming: () => void;
}

export const useMessageStore = create<MessageStore>((set) => ({
  // Initial state
  messages: [],
  isStreaming: false,
  streamingContent: "",
  streamingMessageId: null,

  // Actions
  setMessages: (messages) => set({ messages }),

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    })),

  clearMessages: () => set({ messages: [] }),

  // Streaming
  setIsStreaming: (value) => set({ isStreaming: value }),

  setStreamingContent: (content) => set({ streamingContent: content }),

  appendStreamingContent: (chunk) =>
    set((state) => ({
      streamingContent: state.streamingContent + chunk,
    })),

  setStreamingMessageId: (id) => set({ streamingMessageId: id }),

  resetStreaming: () =>
    set({
      isStreaming: false,
      streamingContent: "",
      streamingMessageId: null,
    }),
}));
