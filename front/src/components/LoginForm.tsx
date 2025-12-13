import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/useAuth";
import { isAxiosError } from "axios";

const Login: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>(() => sessionStorage.getItem("loginError") || "");

  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    if (error) {
      sessionStorage.setItem("loginError", error);
    } else {
      sessionStorage.removeItem("loginError");
    }
  }, [error]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      await login(email, password);
      sessionStorage.removeItem("loginError");
      navigate("/dashboard");
    } catch (err: unknown) {
      console.error("Error en login:", err);
      if (isAxiosError(err)) {
        setError(err.response?.data?.message || "Credenciales incorrectas o error en el servidor.");
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Error desconocido. Inténtalo nuevamente.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-card">

      <form onSubmit={handleSubmit}>
        <div className="mb-1 p-2">
          <label htmlFor="email" className="block mb-1 text-white font-bold text-[15px]">
            Correo
          </label>
          <input
            className="w-full p-3 border border-[#bdc3c7] text-base text-[#000000] rounded-lg"
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="usuario@mail.escuela.edu.co"
            required
          />
        </div>

        <div className="mb-8 p-2">
          <label htmlFor="password" className="block mb-1 text-white font-bold text-[15px]">
            Contraseña
          </label>
          <input
            className="w-full p-3 border border-[#bdc3c7] rounded-lg text-base text-[#000000]"
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="********"
            required
          />
        </div>

        {error && <p className="mb-4 text-center text-red-200 text-sm">{error}</p>}

        <button
          type="submit"
          disabled={isLoading}
          className="bg-blue-950 text-lg w-full p-3 rounded-lg font-medium hover:bg-opacity-90 transition"
        >
          {isLoading ? "Cargando..." : "Iniciar Sesión"}
        </button>

        <div className="mt-6 text-center">
          <Link to="/forgot-password" className="text-xs sm:text-base text-[#7aa6ff]">
            ¿Olvidaste tu contraseña?
          </Link>
        </div>
      </form>
    </div>
  );
};

export default Login;
