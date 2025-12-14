import React, { useState } from 'react';
import Sidebar from '../common/Sidebar';
import FilterBar from '../common/FilterBar';
import { CheckCircle, AlertTriangle, XCircle, TrendingUp, TrendingDown } from 'lucide-react';

const DashboardAdmin: React.FC = () => {
    const [timeRange, setTimeRange] = useState('24h');
    const [sidebarOpen, setSidebarOpen] = useState(true);

    // Mock global system status
    const globalStatus = 'yellow';
    const statusConfig = {
        green: { text: 'All Systems Operating Normally', icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' },
        yellow: { text: 'Minor Issues Detected', icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
        red: { text: 'Critical Issues - Action Required', icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' }
    };

    // KPI mock data
    const kpis = [
        { label: 'Success Rate', value: '94.2%', change: -2.3, status: 'warning' },
        { label: 'Error Rate', value: '5.8%', change: 2.3, status: 'error' },
        { label: 'Transactions', value: '12,847', change: 8.5, status: 'good' },
        { label: 'Conversion', value: '67.3%', change: -1.2, status: 'warning' }
    ];

    // Generate hourly transaction data
    const generateHourlyData = () => {
        const hours = [];
        const now = new Date();
        for (let i = 23; i >= 0; i--) {
            const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
            const hourStr = hour.getHours() + ':00';

            const baseApproved = 600 + Math.random() * 400;
            const baseDeclined = 50 + Math.random() * 100;

            let multiplier = (hour.getHours() >= 14 && hour.getHours() <= 18) ? 0.7 : 1;

            const approved = Math.floor(baseApproved * multiplier);
            const declined = Math.floor(baseDeclined / multiplier);
            const total = approved + declined;

            hours.push({
                time: hourStr,
                approved,
                declined,
                total,
                rate: ((approved / total) * 100).toFixed(1)
            });
        }
        return hours;
    };

    const chartData = generateHourlyData();
    const StatusIcon = statusConfig[globalStatus].icon;

    return (
        <div className="flex h-screen bg-slate-950 text-slate-100">
            {/* Sidebar */}
            <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

            {/* Main Content */}
            <div className="flex-1 overflow-auto">
                <div className="p-8 max-w-[1800px] mx-auto">

                    {/* Header */}
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h1 className="text-3xl font-bold text-white">Payment Health</h1>
                            <p className="text-slate-400 mt-1">Real-time overview of your payment performance</p>
                        </div>
                        <select
                            value={timeRange}
                            onChange={(e) => setTimeRange(e.target.value)}
                            className="px-4 py-2 border border-slate-700 rounded-lg bg-slate-800 text-slate-200 font-medium"
                        >
                            <option value="1h">Last Hour</option>
                            <option value="24h">Last 24 Hours</option>
                            <option value="7d">Last 7 Days</option>
                        </select>
                    </div>

                    {/* Filters */}
                    <FilterBar />

                    {/* Chart */}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
                        {/* Chart header & legend */}
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h3 className="text-lg font-bold text-white mb-1">Transaction Volume & Success Rate</h3>
                                <p className="text-slate-400 text-sm">24-hour view of approved vs declined transactions</p>
                            </div>
                            <div className="flex items-center gap-6 text-sm">
                                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-blue-500" /> <span className="text-slate-300">Total Volume</span></div>
                                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-emerald-500" /> <span className="text-slate-300">Success Rate ≥ 96%</span></div>
                                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-amber-500" /> <span className="text-slate-300">Warning 94-96%</span></div>
                                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-red-500" /> <span className="text-slate-300">Critical &lt; 94%</span></div>
                            </div>
                        </div>

                        {/* Chart area */}
                        <div className="relative h-80 bg-slate-950/50 rounded-lg pt-4 pb-8 px-6 border border-slate-800/50">
                            {/* Y-axis labels */}
                            <div className="absolute left-6 top-8 bottom-12 w-12 flex flex-col justify-between text-xs text-slate-500">
                                <span>1,000</span>
                                <span>750</span>
                                <span>500</span>
                                <span>250</span>
                                <span>0</span>
                            </div>

                            {/* Chart lines and area */}
                            <div className="ml-16 mr-8 h-full relative pb-4">
                                <div className="absolute inset-0 flex flex-col justify-between pb-4">
                                    {[...Array(5)].map((_, i) => (
                                        <div key={i} className="border-t border-slate-800/50 border-dashed" />
                                    ))}
                                </div>

                                <svg className="absolute inset-0 w-full pb-4" style={{ height: 'calc(100% - 1rem)' }} preserveAspectRatio="none">
                                    <defs>
                                        <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                            <stop offset="0%" stopColor="rgb(59, 130, 246)" stopOpacity="0.3" />
                                            <stop offset="100%" stopColor="rgb(59, 130, 246)" stopOpacity="0.05" />
                                        </linearGradient>
                                    </defs>

                                    <path
                                        d={(() => {
                                            const maxTotal = Math.max(...chartData.map(d => d.total));
                                            const points = chartData.map((d, i) => {
                                                const x = (i / (chartData.length - 1)) * 100;
                                                const y = 100 - ((d.total / maxTotal) * 95);
                                                return `${x}% ${y}%`;
                                            }).join(' L ');
                                            return `M 0% 100% L ${points} L 100% 100% Z`;
                                        })()}
                                        fill="url(#areaGradient)"
                                    />

                                    {chartData.map((d, i) => {
                                        if (i === 0) return null;
                                        const prev = chartData[i - 1];
                                        const maxTotal = Math.max(...chartData.map(d => d.total));
                                        const x1 = ((i - 1) / (chartData.length - 1)) * 100;
                                        const y1 = 100 - ((prev.total / maxTotal) * 95);
                                        const x2 = (i / (chartData.length - 1)) * 100;
                                        const y2 = 100 - ((d.total / maxTotal) * 95);

                                        const color = parseFloat(d.rate) >= 96 ? 'rgb(34, 197, 94)' :
                                            parseFloat(d.rate) >= 94 ? 'rgb(251, 191, 36)' :
                                                'rgb(239, 68, 68)';

                                        return <line key={i} x1={`${x1}%`} y1={`${y1}%`} x2={`${x2}%`} y2={`${y2}%`} stroke={color} strokeWidth="3" strokeLinecap="round" />;
                                    })}
                                </svg>

                                {/* Hover points */}
                                <div className="absolute inset-0 flex justify-between pb-4" style={{ height: '100%' }}>
                                    {chartData.map((d, i) => {
                                        const maxTotal = Math.max(...chartData.map(d => d.total));
                                        const topOffset = ((1 - (d.total / maxTotal)) * 95);
                                        const color = parseFloat(d.rate) >= 96 ? 'bg-emerald-500' :
                                            parseFloat(d.rate) >= 94 ? 'bg-amber-500' :
                                                'bg-red-500';
                                        return (
                                            <div key={i} className="flex-1 flex flex-col items-center group cursor-pointer relative">
                                                <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl z-10 whitespace-nowrap pointer-events-none"
                                                     style={{ top: `${topOffset}%`, transform: 'translateY(-100%) translateY(-12px)' }}>
                                                    <div className="text-xs text-slate-400 mb-1">{d.time}</div>
                                                    <div className="text-sm font-bold text-white mb-1">{d.total.toLocaleString()} transactions</div>
                                                    <div className="text-xs text-emerald-400">✓ {d.approved.toLocaleString()} approved</div>
                                                    <div className="text-xs text-red-400">✗ {d.declined.toLocaleString()} declined</div>
                                                    <div className={`text-xs font-semibold mt-1 ${d.rate >= 96 ? 'text-emerald-400' : d.rate >= 94 ? 'text-amber-400' : 'text-red-400'}`}>
                                                        Success Rate: {d.rate}%
                                                    </div>
                                                </div>

                                                <div className={`w-2.5 h-2.5 rounded-full ${color} opacity-0 group-hover:opacity-100 transition-opacity absolute shadow-lg`} style={{ top: `${topOffset}%` }} />
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* X-axis labels */}
                            <div className="absolute bottom-2 left-20 right-8 flex justify-between text-xs text-slate-500">
                                {chartData.filter((_, i) => i % 4 === 0).map((d, i) => (
                                    <span key={i}>{d.time}</span>
                                ))}
                                <span>Now</span>
                            </div>
                        </div>
                    </div>

                    {/* Global Status + KPIs */}
                    <div className="grid grid-cols-5 gap-4 mb-6">
                        <div className={`col-span-1 ${statusConfig[globalStatus].bg} ${statusConfig[globalStatus].border} border rounded-xl p-5 flex flex-col items-center justify-center text-center`}>
                            <StatusIcon className={`w-10 h-10 ${statusConfig[globalStatus].color} mb-2`} />
                            <h3 className={`text-sm font-bold ${statusConfig[globalStatus].color}`}>
                                {globalStatus === 'green' ? 'Healthy' : globalStatus === 'yellow' ? 'Warning' : 'Critical'}
                            </h3>
                            <p className="text-xs text-slate-400 mt-1">System Status</p>
                        </div>

                        {kpis.map((kpi, idx) => (
                            <div key={idx} className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-slate-400 text-sm font-medium">{kpi.label}</span>
                                    {kpi.status === 'error' && <XCircle className="w-4 h-4 text-red-400" />}
                                    {kpi.status === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-400" />}
                                    {kpi.status === 'good' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                                </div>
                                <div className="text-2xl font-bold text-white mb-1">{kpi.value}</div>
                                <div className="flex items-center gap-1">
                                    {kpi.change > 0 ? (
                                        <TrendingUp className={`w-3 h-3 ${kpi.status === 'good' ? 'text-emerald-400' : 'text-red-400'}`} />
                                    ) : (
                                        <TrendingDown className={`w-3 h-3 ${kpi.status === 'good' ? 'text-emerald-400' : 'text-red-400'}`} />
                                    )}
                                    <span className={`text-xs font-medium ${Math.abs(kpi.change) > 2 ? 'text-red-400' : 'text-slate-400'}`}>
                                        {Math.abs(kpi.change)}% vs yesterday
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>

                </div>
            </div>
        </div>
    );
};

export default DashboardAdmin;
