import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  username: string;
  role: string;
  permissions: string[];
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isLoading: true,
      login: async (username: string, password: string) => {
        try {
          const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
            credentials: 'include',
          });

          if (!response.ok) {
            throw new Error('Login failed');
          }

          const user = await response.json();
          set({ user, isLoading: false });
        } catch (error) {
          console.error('Login error:', error);
          throw error;
        }
      },
      logout: async () => {
        await fetch('/api/auth/logout', {
          method: 'POST',
          credentials: 'include',
        });
        set({ user: null });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
