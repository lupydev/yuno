import { useState, type ReactNode } from "react";
import { AuthContext } from "./AuthContext";
import { login as loginService, logout as logoutService } from "../services/authService";
import type { UserData } from "../types/user";

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [role, setRole] = useState<string | null>(null);
  const [user, setUser] = useState<UserData | null>(null);

  const login = async (email: string, password: string) => {
    const response = await loginService(email, password);

    const userData = response.userData;

    if (userData.role === "ADMIN") {
      //const supervisorDetails = await getSupervisorById(userData.id);
      //userData.companyId = supervisorDetails.company.id;
    }

    setUser(userData);
    setRole(userData.role);
    setIsAuthenticated(true);

    document.cookie = `user=${encodeURIComponent(JSON.stringify(userData))}; SameSite=Strict; Secure; max-age=${1800}`;
  };

  const logout = async () => {
    try {
      await logoutService();
    } catch (err) {
      console.warn("Error al cerrar sesión:", err);
    }
    setIsAuthenticated(false);
    setRole(null);
    setUser(null);
    document.cookie = "user=; max-age=0; path=/;";
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, role, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
