import React from 'react';
import { LayoutDashboard, Activity, Users, Bell, Menu } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import logo from '../../assets/yunologo.png';

interface SidebarProps {
    sidebarOpen: boolean;
    setSidebarOpen: (open: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ sidebarOpen, setSidebarOpen }) => {
    const navigate = useNavigate();
    const location = useLocation();

    const navItems = [
        { icon: LayoutDashboard, label: 'Overview', path: '/dashboard' },
        { icon: Users, label: 'Users', path: '/users' },
        { icon: Activity, label: 'Reports', path: '/reports' },
    ];

    return (
        <aside className={`${sidebarOpen ? 'w-56' : 'w-16'} bg-slate-900 border-r border-slate-800 transition-all duration-300 flex flex-col items-stretch`}>
            {/* Logo + Toggle */}
            <div className="px-4 py-5 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <img src={logo} alt="YUNO" className={`${sidebarOpen ? 'w-36' : 'w-6'} object-contain transition-all`} />
                </div>

                <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="p-2 rounded-md hover:bg-slate-800/60 transition"
                    aria-label="Toggle sidebar"
                    title="Toggle sidebar"
                >
                    <Menu className="w-5 h-5 text-slate-300" />
                </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-2 py-4 space-y-1">
                {navItems.map((item) => {
                    const isActive = location.pathname.startsWith(item.path);
                    const Icon = item.icon;
                    return (
                        <button
                            key={item.path}
                            onClick={() => navigate(item.path)}
                            title={!sidebarOpen ? item.label : undefined}
                            className={`flex items-center gap-3 w-full px-3 py-2 rounded-lg transition-colors ${isActive ? 'bg-slate-800/60 ring-1 ring-indigo-500' : 'hover:bg-slate-800/40'} text-slate-200`}
                        >
                            <Icon className={`w-5 h-5 ${isActive ? 'text-indigo-300' : 'text-slate-400'}`} />
                            {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
                        </button>
                    );
                })}
            </nav>

            {/* Footer / Notifications & Profile */}
            <div className="px-3 py-4 border-t border-slate-800 flex items-center gap-3">
                <button
                    className={`p-2 rounded-md hover:bg-slate-800/40 transition ${sidebarOpen ? 'flex items-center gap-3' : ''}`}
                    title={!sidebarOpen ? 'Notifications' : undefined}
                >
                    <Bell className="w-5 h-5 text-slate-300" />
                    {sidebarOpen && <span className="text-sm text-slate-200">Notifications</span>}
                </button>

                {/* simple profile placeholder */}
                <div className="ml-auto flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-white text-sm font-semibold">A</div>
                    {sidebarOpen && <div className="text-sm text-slate-200">Alice</div>}
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
