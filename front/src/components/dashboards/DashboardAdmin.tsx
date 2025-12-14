import React, { useState, useEffect } from 'react';
import FilterBar from '../common/FilterBar';
import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import apiBackClient from '../../services/apiBackClient';

const DashboardAdmin: React.FC = () => {
    const [timeRange, setTimeRange] = useState('24h');
    const [activeTab, setActiveTab] = useState<'dashboard'|'reports'>('dashboard');
    const [selectedAlert, setSelectedAlert] = useState<number | null>(null);
    const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

    // Mock global system status
    const globalStatus: 'green' | 'yellow' | 'red' = 'yellow';
    const statusConfig = {
        green: { text: 'All Systems Operating Normally', icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' },
        yellow: { text: 'Minor Issues Detected', icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
        red: { text: 'Critical Issues - Action Required', icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' }
    };

    // Metrics from backend
    const [metrics, setMetrics] = useState<any | null>(null);
    const [recentEvents, setRecentEvents] = useState<any[]>([]);
    const [loadingMetrics, setLoadingMetrics] = useState(false);
    const [merchantsList, setMerchantsList] = useState<string[]>([]);
    const [providersList, setProvidersList] = useState<string[]>([]);

    // KPI mapping from metrics
    const kpis = metrics ? [
        { label: 'Success Rate', value: `${metrics.success_rate}%`, change: 0, status: metrics.success_rate >= 96 ? 'good' : metrics.success_rate >= 94 ? 'warning' : 'error' },
        { label: 'Error Rate', value: `${(100 - metrics.success_rate).toFixed(2)}%`, change: 0, status: metrics.success_rate >= 96 ? 'good' : 'error' },
        { label: 'Transactions', value: metrics.transaction_volume_usd?.transaction_count?.toLocaleString() || metrics.total_events?.toLocaleString() || '0', change: 0, status: 'good' },
        { label: 'Conversion', value: `${metrics.success_rate?.toFixed ? metrics.success_rate.toFixed(1) : metrics.success_rate}%`, change: 0, status: metrics.success_rate >= 96 ? 'good' : 'warning' }
    ] : [
        { label: 'Success Rate', value: '—', change: 0, status: 'warning' },
        { label: 'Error Rate', value: '—', change: 0, status: 'error' },
        { label: 'Transactions', value: '—', change: 0, status: 'good' },
        { label: 'Conversion', value: '—', change: 0, status: 'warning' }
    ];

    // Generate chart data with dynamic bucketing depending on timeRange
    const generateChartData = () => {
        const now = new Date();
        let bucketCount = 24;
        let intervalMs = 60 * 60 * 1000; // 1 hour
        let totalSpanMs = 24 * 60 * 60 * 1000;

        if (timeRange === '1h') {
            totalSpanMs = 60 * 60 * 1000; // 1 hour
            bucketCount = 6; // 10-minute buckets
            intervalMs = totalSpanMs / bucketCount; // 10 minutes
        } else if (timeRange === '24h') {
            totalSpanMs = 24 * 60 * 60 * 1000;
            bucketCount = 24; // hourly
            intervalMs = totalSpanMs / bucketCount; // 1 hour
        } else if (timeRange === '7d') {
            totalSpanMs = 7 * 24 * 60 * 60 * 1000;
            bucketCount = 7; // daily
            intervalMs = totalSpanMs / bucketCount; // 1 day
        }

        const start = new Date(now.getTime() - totalSpanMs);
        const buckets: Array<any> = [];
        for (let i = 0; i < bucketCount; i++) {
            const bucketStart = new Date(start.getTime() + i * intervalMs);
            // label formatting
            let label = '';
            if (timeRange === '1h') {
                const hh = bucketStart.getHours().toString().padStart(2, '0');
                const mm = bucketStart.getMinutes().toString().padStart(2, '0');
                label = `${hh}:${mm}`;
            } else if (timeRange === '24h') {
                label = `${bucketStart.getHours()}:00`;
            } else if (timeRange === '7d') {
                label = bucketStart.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
            }
            buckets.push({ start: bucketStart, approved: 0, declined: 0, total: 0, rate: '0.0', label });
        }

        // aggregate events
        recentEvents.forEach(ev => {
            const d = new Date(ev.created_at);
            if (d < start || d > now) return;
            const offset = d.getTime() - start.getTime();
            const idx = Math.floor(offset / intervalMs);
            if (idx < 0 || idx >= buckets.length) return;

            const rawFailed = ev.failed;
            const failedBool = rawFailed === true || rawFailed === 'true' || rawFailed === 'True' || rawFailed === '1' || rawFailed === 1;
            const isApproved = typeof rawFailed !== 'undefined' ? !failedBool : (ev.status_category ? ev.status_category === 'approved' : true);

            if (isApproved) buckets[idx].approved += 1;
            else buckets[idx].declined += 1;
            buckets[idx].total += 1;
        });

        // compute rates and map label
        return buckets.map(b => ({ time: b.label, approved: b.approved, declined: b.declined, total: b.total, rate: b.total > 0 ? ((b.approved / b.total) * 100).toFixed(1) : '0.0' }));
    };

    const chartData = generateChartData();

    // Precompute SVG points for total/approved/declined series
    const maxTotal = Math.max(...chartData.map(d => d.total), 1);
    const denom = Math.max(1, chartData.length - 1);

    // Build numeric point arrays for smooth curves
    const ptsTotal = chartData.map((d, i) => ({ x: (i / denom) * 100, y: 100 - ((d.total / maxTotal) * 95) }));
    const ptsApproved = chartData.map((d, i) => ({ x: (i / denom) * 100, y: 100 - ((d.approved / maxTotal) * 95) }));
    const ptsDeclined = chartData.map((d, i) => ({ x: (i / denom) * 100, y: 100 - ((d.declined / maxTotal) * 95) }));

    const buildCurve = (pts: {x:number,y:number}[]) => {
        if (pts.length === 0) return '';
        if (pts.length === 1) return `M ${pts[0].x} ${pts[0].y}`;
        let d = `M ${pts[0].x} ${pts[0].y}`;
        for (let i = 0; i < pts.length - 1; i++) {
            const p = pts[i];
            const q = pts[i + 1];
            const cx1 = (p.x + q.x) / 2;
            const cy1 = p.y;
            const cx2 = (p.x + q.x) / 2;
            const cy2 = q.y;
            d += ` C ${cx1.toFixed(2)} ${cy1.toFixed(2)} ${cx2.toFixed(2)} ${cy2.toFixed(2)} ${q.x.toFixed(2)} ${q.y.toFixed(2)}`;
        }
        return d;
    };

    const curveTotal = buildCurve(ptsTotal);
    const curveApproved = buildCurve(ptsApproved);
    const curveDeclined = buildCurve(ptsDeclined);

    // area path covering total curve
    const areaPath = curveTotal ? `M 0 100 L ${curveTotal.replace(/^M\s*/, '')} L 100 100 Z` : '';


    const [filters, setFilters] = useState<{ merchant: string | null; country: string | null; provider: string | null; method: string | null }>({ merchant: null, country: null, provider: null, method: null });

    useEffect(() => {
        // compute start/end based on selected timeRange
        const now = new Date();
        let startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000); // default 24h
        if (timeRange === '1h') startDate = new Date(now.getTime() - 1 * 60 * 60 * 1000);
        else if (timeRange === '24h') startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        else if (timeRange === '7d') startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        const start = startDate.toISOString();
        const end = now.toISOString();

        const fetchMetrics = async () => {
            try {
                setLoadingMetrics(true);
                // pass filters and date range as query params when available
                const params = new URLSearchParams();
                if (filters.merchant) params.append('merchant', filters.merchant);
                if (filters.provider) params.append('provider', filters.provider);
                if (filters.country) params.append('country', filters.country);
                params.append('start_date', start);
                params.append('end_date', end);
                const resp = await apiBackClient.get(`/analytics/metrics/summary?${params.toString()}`);
                setMetrics(resp.data);
            } catch (err) {
                console.error('Error fetching metrics summary', err);
            } finally {
                setLoadingMetrics(false);
            }
        };

        const fetchLists = async () => {
            try {
                const m = await apiBackClient.get('/analytics/merchants');
                setMerchantsList(m.data.merchants || []);
            } catch (err) {
                console.error('Error fetching merchants list', err);
            }
            try {
                const p = await apiBackClient.get('/analytics/providers');
                // providers endpoint returns array of { provider, merchants }
                const providers = (p.data.providers || []).map((x: any) => x.provider);
                setProvidersList(providers);
            } catch (err) {
                console.error('Error fetching providers list', err);
            }
        };

        const fetchRecent = async () => {
            try {
                // Single request returning all matching events (no limit)
                const params = new URLSearchParams();
                params.append('start_date', start);
                params.append('end_date', end);
                if (filters.merchant) params.append('merchant', filters.merchant);
                if (filters.provider) params.append('provider', filters.provider);
                if (filters.country) params.append('country', filters.country);
                if (filters.method) params.append('payment_method', filters.method);

                const resp = await apiBackClient.get(`/analytics/events/all?${params.toString()}`);
                const events = resp.data.transactions || [];
                const normalized = events.map((e: any) => ({ ...e, created_at: e.date || e.created_at }));
                setRecentEvents(normalized);
                if (!normalized || normalized.length === 0) {
                    console.warn('No recent events returned from analytics/events/all for selected range');
                }
            } catch (err) {
                console.error('Error fetching recent events', err);
            }
        };

        fetchLists();
        fetchMetrics();
        fetchRecent();
    }, [filters, timeRange]);
    const StatusIcon = statusConfig[globalStatus].icon;

    return (
        <div className="flex-1 bg-slate-900 text-slate-100 antialiased min-h-full">

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
                    <FilterBar onChange={setFilters} merchants={merchantsList} providers={providersList} />

                    {/* Chart */}
                    <div className="bg-gradient-to-b from-slate-900/60 to-slate-900/40 rounded-xl p-6 mb-6 shadow-sm border border-slate-800/20">
                        {/* Chart header & legend */}
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h3 className="text-lg font-bold text-white mb-1">Transaction Volume & Success Rate</h3>
                                <p className="text-slate-400 text-sm">24-hour view of approved vs declined transactions</p>
                            </div>
                            <div className="flex items-center gap-6 text-sm">
                                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-blue-500" /> <span className="text-slate-300">Total</span></div>
                                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-emerald-500" /> <span className="text-slate-300">Approved</span></div>
                                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-red-500" /> <span className="text-slate-300">Declined</span></div>
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
                                    {[...Array(4)].map((_, i) => (
                                        <div key={i} className="border-t border-slate-800/40" />
                                    ))}
                                </div>

                                <svg className="absolute inset-0 w-full pb-4" style={{ height: 'calc(100% - 1rem)' }} preserveAspectRatio="none" viewBox="0 0 100 100">
                                    <defs>
                                        <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                            <stop offset="0%" stopColor="rgb(59, 130, 246)" stopOpacity="0.08" />
                                            <stop offset="100%" stopColor="rgb(59, 130, 246)" stopOpacity="0.01" />
                                        </linearGradient>
                                    </defs>

                                    {areaPath && <path d={areaPath} fill="url(#areaGradient)" fillOpacity="0.06" />} 

                                    {curveTotal && <path d={curveTotal} stroke="#3b82f6" strokeWidth={1} strokeOpacity={0.95} strokeLinecap="round" strokeLinejoin="round" fill="none" />} 
                                    {curveApproved && <path d={curveApproved} stroke="#10b981" strokeWidth={1} strokeOpacity={0.95} strokeLinecap="round" strokeLinejoin="round" fill="none" />} 
                                    {curveDeclined && <path d={curveDeclined} stroke="#ef4444" strokeWidth={1} strokeOpacity={0.95} strokeLinecap="round" strokeLinejoin="round" fill="none" />}
                                </svg>

                                {/* Hover capture zones (one per bucket) and a single tooltip/markers shown for hoveredIndex */}
                                <div className="absolute inset-0 flex justify-between pb-4" style={{ height: '100%' }}>
                                    {chartData.map((_, i) => (
                                        <div
                                            key={i}
                                            className="flex-1 h-full"
                                            onMouseEnter={() => setHoveredIndex(i)}
                                            onMouseLeave={() => setHoveredIndex(null)}
                                        />
                                    ))}

                                    {hoveredIndex !== null && (() => {
                                        const d = chartData[hoveredIndex];
                                        const maxT = Math.max(...chartData.map(c => c.total), 1);
                                        const denomLoc = Math.max(1, chartData.length - 1);
                                        const xPerc = (hoveredIndex / denomLoc) * 100;
                                        const topTotal = (1 - (d.total / maxT)) * 95;
                                        const topApproved = (1 - (d.approved / maxT)) * 95;
                                        const topDeclined = (1 - (d.declined / maxT)) * 95;

                                        return (
                                            <>
                                                {/* Tooltip box positioned above total point */}
                                                <div
                                                    style={{ left: `${xPerc}%`, top: `${topTotal}%`, transform: 'translate(-50%, -100%)' }}
                                                    className="absolute pointer-events-none z-20"
                                                >
                                                    <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl text-left text-sm text-slate-200">
                                                        <div className="text-xs text-slate-400 mb-1">{d.time}</div>
                                                        <div className="text-sm font-bold text-white mb-1">Total: {d.total.toLocaleString()}</div>
                                                        <div className="text-xs text-emerald-400">Approved: {d.approved.toLocaleString()}</div>
                                                        <div className="text-xs text-red-400">Declined: {d.declined.toLocaleString()}</div>
                                                        <div className={`text-xs font-semibold mt-1 ${parseFloat(d.rate) >= 96 ? 'text-emerald-400' : parseFloat(d.rate) >= 94 ? 'text-amber-400' : 'text-red-400'}`}>
                                                            Success Rate: {d.rate}%
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Markers for each series */}
                                                <div style={{ left: `${xPerc}%`, top: `${topTotal}%`, transform: 'translate(-50%, -50%)' }} className="absolute z-10">
                                                    <div className="w-3 h-3 rounded-full bg-blue-500 border border-white" />
                                                </div>
                                                <div style={{ left: `${xPerc}%`, top: `${topApproved}%`, transform: 'translate(-50%, -50%)' }} className="absolute z-10">
                                                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 border border-white" />
                                                </div>
                                                <div style={{ left: `${xPerc}%`, top: `${topDeclined}%`, transform: 'translate(-50%, -50%)' }} className="absolute z-10">
                                                    <div className="w-2.5 h-2.5 rounded-full bg-red-400 border border-white" />
                                                </div>
                                            </>
                                        );
                                    })()}
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
                                    {globalStatus === 'yellow' ? 'Warning' : globalStatus === 'red' ? 'Critical' : 'Healthy'}
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
