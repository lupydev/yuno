import type { UserData } from "../types/user";

export interface AuthContextType {
  isAuthenticated: boolean;
  role: string | null;
  user: UserData | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}
