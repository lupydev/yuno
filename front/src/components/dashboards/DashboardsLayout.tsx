// DashboardLayout.tsx
import React, { useState } from 'react';
import { LayoutDashboard, Activity, Bell, Menu, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface DashboardLayoutProps {
    children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const navigate = useNavigate();

    const navItems = [
        { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
        { label: 'Reports', icon: Activity, path: '/reports' },
        { label: 'Users', icon: Users, path: '/users' },
    ];

    return (
        <div className="flex h-screen bg-slate-900 text-white">
            {/* Sidebar */}
            <div className={`bg-slate-950 p-4 flex flex-col transition-all ${sidebarOpen ? 'w-64' : 'w-20'}`}>
                <button onClick={() => setSidebarOpen(!sidebarOpen)} className="mb-6">
                    <Menu className="w-6 h-6" />
                </button>
                <nav className="flex-1 flex flex-col gap-2">
                    {navItems.map((item, idx) => (
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
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto p-8">{children}</div>
        </div>
    );
};
