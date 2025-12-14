// DashboardLayout.tsx
import React, { useState } from 'react';
import { LayoutDashboard, Activity, Bell, Menu, Users, LogOut } from 'lucide-react';
import ThemeToggle from '../common/ThemeToggle';
import { useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/useAuth';


export const DashboardLayout: React.FC = () => {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const navigate = useNavigate();
    const { role, logout, user } = useAuth();

    const navItems = [
        { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard', roles: ['ADMIN', 'DEVELOPER'] },
        { label: 'Reports', icon: Activity, path: '/reports', roles: ['ADMIN', 'DEVELOPER'] },
        { label: 'Users', icon: Users, path: '/users', roles: ['ADMIN'] }, // Solo ADMIN
    ];

    // Filtrar items según el rol
    const filteredNavItems = navItems.filter(item => 
        role && item.roles.includes(role)
    );

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <div className="flex h-screen bg-slate-900 text-white">
            {/* Sidebar */}
            <div className={`bg-slate-950 p-4 flex flex-col transition-all ${sidebarOpen ? 'w-64' : 'w-20'}`}>
                <div className="mb-6 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 hover:bg-slate-800 rounded-lg">
                            <Menu className="w-6 h-6" />
                        </button>
                    </div>
                    {sidebarOpen && (
                        <div className="mt-4">
                            <h1 className="text-2xl font-bold">YUNO</h1>
                            <p className="text-sm text-slate-400 mt-1">{user?.email}</p>
                            <span className="inline-block mt-2 px-2 py-1 text-xs bg-blue-600 rounded">{role}</span>
                        </div>
                    )}
                </div>

                <nav className="flex-1 flex flex-col gap-2">
                    {filteredNavItems.map((item, idx) => (
                        <button
                            key={idx}
                            onClick={() => navigate(item.path)}
                            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors"
                        >
                            <item.icon className="w-5 h-5" />
                            {sidebarOpen && <span>{item.label}</span>}
                        </button>
                    ))}
                </nav>

                {/* Logout */}
                <div className="pt-4 border-t border-slate-800">
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-red-900 transition-colors text-red-400"
                    >
                        <LogOut className="w-5 h-5" />
                        {sidebarOpen && <span>Cerrar Sesión</span>}
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto relative pr-12 pt-6">
                <div className="absolute top-4 right-6 z-30">
                    <ThemeToggle />
                </div>
                <Outlet />
            </div>
        </div>
    );
};
