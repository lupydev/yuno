import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/useAuth";
import { useTheme } from '../contexts/ThemeContext';
import { isAxiosError } from "axios";

const Login: React.FC = () => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string>(
        () => sessionStorage.getItem("loginError") || ""
    );

    const navigate = useNavigate();
    const { login } = useAuth();
    const { theme, setTheme } = useTheme();

    useEffect(() => {
        // force dark theme on login page and restore previous on unmount
        const prev = theme;
        if (theme !== 'dark') setTheme('dark');
        return () => { setTheme(prev); };
    }, []);


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
            console.error("Login error:", err);
            if (isAxiosError(err)) {
                setError(
                    err.response?.data?.message ||
                    "Invalid credentials or server error."
                );
            } else if (err instanceof Error) {
                setError(err.message);
            } else {
                setError("Unknown error. Please try again.");
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-screen h-screen bg-slate-900 overflow-hidden">
            <div className="w-full h-full grid grid-cols-1 md:grid-cols-2">

                {/* Left – Branding */}
                <div className="hidden md:flex items-center justify-center bg-gradient-to-b from-slate-800 to-slate-900 p-12">
                    <div className="max-w-sm text-center">
                        <div className="text-4xl font-extrabold text-white mb-4">YUNO</div>
                        <p className="text-slate-300">
                            Insights and reliability for payments — monitor, diagnose and act quickly.
                        </p>
                    </div>
                </div>

                {/* Right – Form */}
                <div className="flex items-center justify-center p-8">
                    <div className="w-full max-w-md bg-slate-900/80 border border-slate-800 rounded-2xl p-8 shadow-xl">
                        <div className="mb-6 text-center">
                            <h1 className="text-3xl font-bold text-white">Sign in</h1>
                            <p className="text-sm text-slate-400 mt-1">Access your dashboard</p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label htmlFor="email" className="block mb-2 text-sm font-medium text-slate-300">Email</label>
                                <input
                                    id="email"
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="you@company.com"
                                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-600"
                                />
                            </div>

                            <div>
                                <label htmlFor="password" className="block mb-2 text-sm font-medium text-slate-300">Password</label>
                                <input
                                    id="password"
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-600"
                                />
                            </div>

                            {error && <p className="text-center text-red-400 text-sm">{error}</p>}

                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full mt-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-70"
                            >
                                {isLoading ? "Signing in..." : "Sign In"}
                            </button>

                            <div className="mt-4 flex items-center justify-between text-sm">
                                <Link to="/forgot-password" className="text-indigo-300 hover:text-indigo-200">Forgot password?</Link>
                                <Link to="/signup" className="text-slate-400 hover:text-slate-200">Create account</Link>
                            </div>
                        </form>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default Login;
