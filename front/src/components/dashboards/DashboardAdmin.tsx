import React, { useState } from 'react';
import Sidebar from '../common/Sidebar';
import FilterBar from '../common/FilterBar';
import { CheckCircle, AlertTriangle, XCircle, TrendingUp, TrendingDown } from 'lucide-react';

const DashboardAdmin: React.FC = () => {
    const [timeRange, setTimeRange] = useState('24h');
    const [activeTab, setActiveTab] = useState<'dashboard'|'reports'>('dashboard');
    const [selectedAlert, setSelectedAlert] = useState<number | null>(null);

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
        <div className="flex h-screen bg-slate-900 text-slate-100 antialiased">

            {/* Main Content */}
            <div className="flex-1 overflow-auto">
                <div className="p-8 max-w-[1800px] mx-auto">

                    {/* Header */}
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h1 className="text-3xl font-bold text-white">Payment Health</h1>
                            <p className="text-slate-400 mt-1">Real-time overview of your payment performance</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <select
                                value={timeRange}
                                onChange={(e) => setTimeRange(e.target.value)}
                                className="px-3 py-2 rounded-md bg-slate-800/60 text-slate-200 font-medium border border-transparent hover:border-slate-700 transition"
                            >
                                <option value="1h">Last Hour</option>
                                <option value="24h">Last 24 Hours</option>
                                <option value="7d">Last 7 Days</option>
                            </select>
                            <button className="px-3 py-2 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition">Export</button>
                        </div>
                    </div>

                    {/* Filters */}
                    <FilterBar />

                    {/* Chart */}
                    <div className="bg-gradient-to-b from-slate-900/60 to-slate-900/40 rounded-xl p-6 mb-6 shadow-sm border border-slate-800/20">
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

                    {/* Global Status + Alerts */}
                    {activeTab === 'dashboard' ? (
                        <div className="grid grid-cols-5 gap-4 mb-6">
                            <div className={`col-span-1 ${statusConfig[globalStatus].bg} ${statusConfig[globalStatus].border} border rounded-xl p-5 flex flex-col items-center justify-center text-center`}>
                                <StatusIcon className={`w-10 h-10 ${statusConfig[globalStatus].color} mb-2`} />
                                <h3 className={`text-sm font-bold ${statusConfig[globalStatus].color}`}>
                                    {globalStatus === 'green' ? 'Healthy' : globalStatus === 'yellow' ? 'Warning' : 'Critical'}
                                </h3>
                                <p className="text-xs text-slate-400 mt-1">System Status</p>
                            </div>

                            {kpis.map((kpi, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => { setSelectedAlert(idx); setActiveTab('reports'); }}
                                    className={`text-left rounded-lg p-4 bg-gradient-to-br from-slate-800/60 to-slate-900/20 shadow-lg ring-1 ring-slate-700/40 hover:shadow-2xl transform hover:-translate-y-1 transition duration-150 border border-transparent ${kpi.status === 'error' ? 'border-l-red-500' : kpi.status === 'warning' ? 'border-l-amber-500' : 'border-l-emerald-500'}`}
                                >
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className={`w-2 h-2 rounded-full ${kpi.status === 'error' ? 'bg-red-500' : kpi.status === 'warning' ? 'bg-amber-400' : 'bg-emerald-400'}`} />
                                                <span className="inline-block text-xs font-semibold text-amber-400">Alert</span>
                                            </div>
                                            <div className="mt-1 text-sm font-bold text-white">{kpi.label}</div>
                                            <div className="text-xs text-slate-400 mt-1">{kpi.status === 'error' ? 'Critical failures detected' : kpi.status === 'warning' ? 'Intermittent issues observed' : 'Minor anomalies'}</div>
                                        </div>

                                        <div className="flex flex-col items-end ml-6">
                                            <div className="text-xs bg-slate-800/60 rounded-full px-3 py-1 text-slate-200">{Math.abs(kpi.change)} reports</div>
                                            <div className="text-sm font-bold text-white mt-2">{kpi.value}</div>
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    ) : (
                        <div className="mb-6">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-lg font-bold">Reports — {selectedAlert !== null ? kpis[selectedAlert].label : 'Selected'}</h3>
                                <div className="flex items-center gap-2">
                                    <button onClick={() => { setActiveTab('dashboard'); setSelectedAlert(null); }} className="text-sm px-3 py-1 rounded-md bg-slate-800/50 hover:bg-slate-800/60 transition">Back</button>
                                </div>
                            </div>

                            <div className="bg-slate-900 rounded-xl p-4 border border-slate-800/30">
                                <p className="text-sm text-slate-400">Showing recent reports related to this alert. Click any item for full details.</p>
                                <ul className="mt-3 space-y-2">
                                    <li className="p-3 bg-slate-800/30 rounded-md">Report — Example failure log (ID: 001)</li>
                                    <li className="p-3 bg-slate-800/30 rounded-md">Report — Transaction spike analysis (ID: 002)</li>
                                    <li className="p-3 bg-slate-800/30 rounded-md">Report — Downstream service timeout (ID: 003)</li>
                                </ul>
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
};

export default DashboardAdmin;
