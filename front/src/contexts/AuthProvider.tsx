import { useState, useEffect, type ReactNode } from "react";
import { AuthContext } from "./AuthContext";
import { login as loginService, logout as logoutService } from "../services/authService";
import type { UserData } from "../types/user";

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [role, setRole] = useState<string | null>(null);
  const [user, setUser] = useState<UserData | null>(null);

  // Recuperar sesión al cargar la aplicación
  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');

    if (token && storedUser) {
      try {
        const userData: UserData = JSON.parse(storedUser);
        
        // Verificar que el token no esté expirado
        const tokenParts = token.split('.');
        if (tokenParts.length === 3) {
          try {
            const payload = JSON.parse(atob(tokenParts[1]));
            const currentTime = Math.floor(Date.now() / 1000);
            
            if (payload.exp && payload.exp > currentTime) {
              // Token válido, restaurar sesión
              setUser(userData);
              setRole(userData.role);
              setIsAuthenticated(true);
              return;
            }
          } catch (e) {
            console.error('Error decodificando token:', e);
          }
        }
        
        // Si llegamos aquí, el token es inválido o expirado
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
      } catch (error) {
        console.error('Error al recuperar sesión:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
      }
    }
  }, []);

  const login = async (email: string, password: string) => {
    const response = await loginService(email, password);

    console.log('📦 Respuesta del login:', response);

    if (!response || !response.token) {
      throw new Error('Respuesta del servidor inválida: falta token');
    }

    const userData = response.user_data;

    if (!userData) {
      throw new Error('Respuesta del servidor inválida: falta información del usuario');
    }

    // Guardar tokens en localStorage
    localStorage.setItem('token', response.token);
    if (response.refresh_token) {
      localStorage.setItem('refreshToken', response.refresh_token);
    }
    localStorage.setItem('user', JSON.stringify(userData));

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
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
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
