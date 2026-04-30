/**
 * Chat Zustand store for UI state
 */

import { create } from "zustand";

interface ChatStore {
  // State
  activeChatId: string | null;
  titleLoadingIds: Set<string>;

  // Actions
  setActiveChatId: (id: string | null) => void;
  addTitleLoading: (id: string) => void;
  removeTitleLoading: (id: string) => void;
  isTitleLoading: (id: string) => boolean;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  // Initial state
  activeChatId: null,
  titleLoadingIds: new Set(),

  // Actions
  setActiveChatId: (id) => set({ activeChatId: id }),

  addTitleLoading: (id) =>
    set((state) => ({
      titleLoadingIds: new Set([...state.titleLoadingIds, id]),
    })),

  removeTitleLoading: (id) =>
    set((state) => {
      const newSet = new Set(state.titleLoadingIds);
      newSet.delete(id);
      return { titleLoadingIds: newSet };
    }),

  isTitleLoading: (id) => {
    return get().titleLoadingIds.has(id);
  },
}));
