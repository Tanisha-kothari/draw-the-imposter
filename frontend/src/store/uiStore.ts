import { create } from 'zustand';

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface UIStore {
  isDarkMode: boolean;
  toasts: Toast[];
  isLoading: boolean;
  modalContent: string | null;
  
  toggleDarkMode: () => void;
  addToast: (message: string, type: Toast['type']) => void;
  removeToast: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setModal: (content: string | null) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  isDarkMode: true,
  toasts: [],
  isLoading: false,
  modalContent: null,

  toggleDarkMode: () => set((s) => ({ isDarkMode: !s.isDarkMode })),
  addToast: (message, type) => {
    const id = Math.random().toString(36).slice(2);
    set((s) => ({ toasts: [...s.toasts, { id, message, type }] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 4000);
  },
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  setLoading: (loading) => set({ isLoading: loading }),
  setModal: (content) => set({ modalContent: content }),
}));
