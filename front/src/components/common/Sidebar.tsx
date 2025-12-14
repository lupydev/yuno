import React from 'react';
import { LayoutDashboard, Activity, Users, Bell, Menu } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface SidebarProps {
    sidebarOpen: boolean;
    setSidebarOpen: (open: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ sidebarOpen, setSidebarOpen }) => {
    const navigate = useNavigate();

    const navItems = [
        { icon: LayoutDashboard, label: 'Overview', path: '/dashboard' },
        { icon: Users, label: 'Users', path: '/users' },
        { icon: Activity, label: 'Reports', path: '/reports' },
    ];

    return (
        <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-slate-900 border-r border-slate-800 transition-all duration-300 flex flex-col`}>
            {/* Logo + Toggle */}
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                {sidebarOpen && <div className="text-2xl font-bold text-white">YUNO</div>}
                <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 hover:bg-slate-800 rounded-lg">
                    <Menu className="w-5 h-5" />
                </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-2">
                {navItems.map((item, idx) => (
                    <button
                        key={idx}
                        onClick={() => navigate(item.path)}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                            ${item.label === 'Overview' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}
                        `}
                    >
                        <item.icon className="w-5 h-5" />
                        {sidebarOpen && <span className="font-medium">{item.label}</span>}
                    </button>
                ))}
            </nav>

            {/* Notifications */}
            <div className="p-4 border-t border-slate-800">
                <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors">
                    <Bell className="w-5 h-5" />
                    {sidebarOpen && <span className="font-medium">Notifications</span>}
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
