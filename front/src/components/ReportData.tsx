import React, { useState, useRef } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { CheckCircle, AlertCircle, Clock, BarChart3, Eye, EyeOff } from 'lucide-react';

interface ReportData {
    title: string;
    aiDescription: string;
    humanChecked: boolean;
    status: 'pending' | 'in-progress' | 'resolved' | 'rejected';
    aiSolution: string;
    humanSolution: string;
    humanBy?: string;
    date: string;
    approvalDistribution: Array<{ status: string; count: number }>;
    successRate: Array<{ hour: string; rate: number }>;
    cause: {
        type: 'yuno' | 'provider' | 'client';
        details?: {
            yunoComponent?: 'core' | 'integration';
            providerName?: string;
            clientName?: string;
            missingParams?: string[];
        };
    };
    failedTransactions: Array<{ hour: string; count: number }>;
    latency: Array<{ hour: string; ms: number }>;
    technicalErrors: Array<{ hour: string; '400': number; '500': number; '502': number; '503': number; '504': number }>;
}

const TransactionReport: React.FC = () => {
    const [reportData] = useState<ReportData>({
        title: 'Payment Gateway Timeout Issue',
        aiDescription: 'Detected recurring timeout errors in payment processing between 14:00-18:00, affecting approximately 23% of transactions. The issue appears to be related to increased latency in the payment provider integration layer.',
        humanChecked: true,
        status: 'in-progress',
        aiSolution: 'Implement retry mechanism with exponential backoff. Increase timeout threshold from 5s to 10s during peak hours. Add circuit breaker pattern to prevent cascading failures.',
        humanSolution: 'After analysis, confirmed AI recommendation. Additionally implementing request queuing system and adding fallback provider. ETA: 48 hours.',
        humanBy: 'Alice Johnson',
        date: '2025-12-13T14:30:00',
        approvalDistribution: [
            { status: 'Approved', count: 1245 },
            { status: 'Not Approved', count: 678 },
            { status: 'Indeterminate', count: 234 }
        ],
        successRate: [
            { hour: '00:00', rate: 94.5 },
            { hour: '01:00', rate: 95.8 },
            { hour: '02:00', rate: 96.2 },
            { hour: '03:00', rate: 97.1 },
            { hour: '04:00', rate: 96.5 },
            { hour: '05:00', rate: 93.2 },
            { hour: '06:00', rate: 89.7 },
            { hour: '07:00', rate: 84.3 },
            { hour: '08:00', rate: 78.9 },
            { hour: '09:00', rate: 73.4 },
            { hour: '10:00', rate: 68.2 },
            { hour: '11:00', rate: 70.1 },
            { hour: '12:00', rate: 67.5 },
            { hour: '13:00', rate: 64.8 },
            { hour: '14:00', rate: 58.3 },
            { hour: '15:00', rate: 54.2 },
            { hour: '16:00', rate: 56.7 },
            { hour: '17:00', rate: 62.1 },
            { hour: '18:00', rate: 68.9 },
            { hour: '19:00', rate: 75.6 },
            { hour: '20:00', rate: 82.3 },
            { hour: '21:00', rate: 87.9 },
            { hour: '22:00', rate: 91.4 },
            { hour: '23:00', rate: 93.7 }
        ],
        cause: {
            type: 'yuno',
            details: {
                yunoComponent: 'integration',
                providerName: 'PayU',
                clientName: 'McDonald\'s',
                missingParams: ['callback_url', 'merchant_reference']
            }
        },
        failedTransactions: [
            { hour: '00:00', count: 12 },
            { hour: '01:00', count: 8 },
            { hour: '02:00', count: 5 },
            { hour: '03:00', count: 3 },
            { hour: '04:00', count: 7 },
            { hour: '05:00', count: 15 },
            { hour: '06:00', count: 23 },
            { hour: '07:00', count: 45 },
            { hour: '08:00', count: 67 },
            { hour: '09:00', count: 89 },
            { hour: '10:00', count: 103 },
            { hour: '11:00', count: 98 },
            { hour: '12:00', count: 112 },
            { hour: '13:00', count: 134 },
            { hour: '14:00', count: 178 },
            { hour: '15:00', count: 201 },
            { hour: '16:00', count: 195 },
            { hour: '17:00', count: 167 },
            { hour: '18:00', count: 145 },
            { hour: '19:00', count: 98 },
            { hour: '20:00', count: 76 },
            { hour: '21:00', count: 54 },
            { hour: '22:00', count: 34 },
            { hour: '23:00', count: 21 }
        ],
        latency: [
            { hour: '00:00', ms: 245 },
            { hour: '01:00', ms: 231 },
            { hour: '02:00', ms: 198 },
            { hour: '03:00', ms: 187 },
            { hour: '04:00', ms: 203 },
            { hour: '05:00', ms: 298 },
            { hour: '06:00', ms: 456 },
            { hour: '07:00', ms: 678 },
            { hour: '08:00', ms: 892 },
            { hour: '09:00', ms: 1123 },
            { hour: '10:00', ms: 1456 },
            { hour: '11:00', ms: 1389 },
            { hour: '12:00', ms: 1567 },
            { hour: '13:00', ms: 1892 },
            { hour: '14:00', ms: 2345 },
            { hour: '15:00', ms: 2678 },
            { hour: '16:00', ms: 2543 },
            { hour: '17:00', ms: 2234 },
            { hour: '18:00', ms: 1876 },
            { hour: '19:00', ms: 1345 },
            { hour: '20:00', ms: 987 },
            { hour: '21:00', ms: 765 },
            { hour: '22:00', ms: 543 },
            { hour: '23:00', ms: 376 }
        ],
        technicalErrors: [
            { hour: '00:00', '400': 2, '500': 1, '502': 0, '503': 1, '504': 2 },
            { hour: '01:00', '400': 1, '500': 0, '502': 1, '503': 0, '504': 1 },
            { hour: '02:00', '400': 0, '500': 1, '502': 0, '503': 0, '504': 1 },
            { hour: '03:00', '400': 1, '500': 0, '502': 0, '503': 1, '504': 0 },
            { hour: '04:00', '400': 2, '500': 1, '502': 1, '503': 0, '504': 1 },
            { hour: '05:00', '400': 3, '500': 2, '502': 1, '503': 2, '504': 3 },
            { hour: '06:00', '400': 5, '500': 3, '502': 2, '503': 3, '504': 5 },
            { hour: '07:00', '400': 8, '500': 5, '502': 4, '503': 6, '504': 9 },
            { hour: '08:00', '400': 12, '500': 8, '502': 6, '503': 9, '504': 14 },
            { hour: '09:00', '400': 15, '500': 11, '502': 9, '503': 12, '504': 18 },
            { hour: '10:00', '400': 18, '500': 14, '502': 11, '503': 15, '504': 22 },
            { hour: '11:00', '400': 17, '500': 13, '502': 10, '503': 14, '504': 20 },
            { hour: '12:00', '400': 19, '500': 15, '502': 12, '503': 16, '504': 24 },
            { hour: '13:00', '400': 22, '500': 18, '502': 14, '503': 19, '504': 28 },
            { hour: '14:00', '400': 28, '500': 23, '502': 18, '503': 25, '504': 35 },
            { hour: '15:00', '400': 32, '500': 27, '502': 21, '503': 29, '504': 41 },
            { hour: '16:00', '400': 31, '500': 26, '502': 20, '503': 28, '504': 39 },
            { hour: '17:00', '400': 27, '500': 22, '502': 17, '503': 24, '504': 33 },
            { hour: '18:00', '400': 23, '500': 19, '502': 15, '503': 20, '504': 29 },
            { hour: '19:00', '400': 16, '500': 13, '502': 10, '503': 14, '504': 20 },
            { hour: '20:00', '400': 12, '500': 10, '502': 8, '503': 11, '504': 15 },
            { hour: '21:00', '400': 9, '500': 7, '502': 5, '503': 8, '504': 11 },
            { hour: '22:00', '400': 6, '500': 4, '502': 3, '503': 5, '504': 7 },
            { hour: '23:00', '400': 3, '500': 2, '502': 1, '503': 2, '504': 4 }
        ]
    });

    const [aiHidden, setAiHidden] = useState(false);

    const statusColors = {
        pending: 'bg-slate-700 text-slate-300',
        'in-progress': 'bg-indigo-900 text-indigo-300',
        resolved: 'bg-emerald-900 text-emerald-300',
        rejected: 'bg-red-900 text-red-300'
    };

    const pieColors = ['#10b981', '#ef4444', '#f59e0b'];

    const graphsRef = useRef<HTMLDivElement>(null);
    const [activeChart, setActiveChart] = useState<'failed'|'latency'|'technical'|'approval'|'success'>('failed');

    const scrollToGraphs = () => {
        graphsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    return (
        <div className="min-h-screen bg-slate-900 p-6 antialiased text-slate-100">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3 text-sm text-slate-400">
                        <span className="px-2 py-1 bg-slate-800/40 rounded-md text-slate-200">Reports</span>
                        <span className="text-slate-500">/</span>
                        <span className="text-slate-300 font-medium">{reportData.cause.details?.clientName || 'Merchant'}</span>
                        <span className="text-slate-500">/</span>
                        <span className="text-slate-300">{reportData.title}</span>
                    </div>
                    <button className="text-sm px-3 py-1 bg-slate-800/40 rounded-md hover:bg-slate-800/50">Back to list</button>
                </div>
                <div className="relative bg-gradient-to-b from-slate-900/60 to-slate-900/40 rounded-xl shadow-sm p-6 border border-slate-800/20 ring-1 ring-slate-700/30">
                    <div className="mb-3 flex items-center gap-3">
                        <span className="text-xs px-2 py-1 bg-indigo-600 text-white rounded-md">REPORT</span>
                        <span className="text-xs text-slate-400">Viewing detailed findings</span>
                    </div>
                    <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                            <h1 className="text-3xl font-bold text-white mb-2">{reportData.title}</h1>
                            <div className="flex items-center gap-4 text-sm text-slate-400">
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                    {new Date(reportData.date).toLocaleString()}
                </span>
                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColors[reportData.status]}`}>
                  {reportData.status.toUpperCase()}
                </span>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            {reportData.humanChecked ? (
                                <div className="flex items-center gap-2 px-3 py-2 bg-emerald-900/20 rounded-md border border-emerald-800/30">
                                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                                    <span className="text-sm font-medium text-emerald-300">Human Verified</span>
                                </div>
                            ) : (
                                <div className="flex items-center gap-2 px-3 py-2 bg-amber-900/20 rounded-md border border-amber-800/30">
                                    <AlertCircle className="w-5 h-5 text-amber-400" />
                                    <span className="text-sm font-medium text-amber-300">Pending Review</span>
                                </div>
                            )}

                        </div>
                    </div>

                    { !aiHidden ? (
                        <div className="mb-6 p-6 rounded-lg bg-indigo-600/10 border-l-4 border-indigo-500">
                            <div className="flex items-start justify-between">
                                <div className="flex items-start gap-4">
                                    <AlertCircle className="w-6 h-6 text-indigo-400 mt-1" />
                                    <div>
                                        <h3 className="text-lg font-semibold text-indigo-200">AI Analysis — Recommended Action</h3>
                                        <p className="text-sm text-slate-200 mt-2 leading-relaxed max-w-3xl">{reportData.aiDescription}</p>
                                    </div>
                                </div>
                                <div>
                                    <button onClick={() => setAiHidden(true)} className="p-2 rounded-md bg-slate-800/30 hover:bg-slate-800/40 transition" aria-label="Hide AI analysis">
                                        <EyeOff className="w-5 h-5 text-slate-200" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="mb-6 flex justify-end">
                            <button onClick={() => setAiHidden(false)} className="p-2 rounded-md bg-slate-800/30 hover:bg-slate-800/40 transition" aria-label="Show AI analysis">
                                <Eye className="w-5 h-5 text-slate-200" />
                            </button>
                        </div>
                    )}

                </div>

                {/* Cause Analysis */}
                <div className="bg-gradient-to-b from-slate-900/60 to-slate-900/40 rounded-xl shadow-sm p-6 border border-slate-800/20">
                    <h2 className="text-xl font-bold text-gray-100 mb-4">Root Cause Analysis</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="border border-slate-800/30 rounded-lg p-4 bg-slate-900/40">
                            <span className="text-sm font-medium text-slate-400">Responsible Party</span>
                            <p className="text-lg font-semibold text-white mt-1 capitalize">{reportData.cause.type}</p>
                            {reportData.cause.type === 'yuno' && reportData.cause.details?.yunoComponent && (
                                <span className="inline-block mt-2 px-3 py-1 bg-purple-900/40 text-purple-300 text-xs font-medium rounded-full border border-purple-800">
                  {reportData.cause.details.yunoComponent.toUpperCase()}
                </span>
                            )}
                        </div>
                        <div className="border border-slate-800/30 rounded-lg p-4 bg-slate-900/40">
                            <span className="text-sm font-medium text-slate-400">Provider</span>
                            <p className="text-lg font-semibold text-white mt-1">{reportData.cause.details?.providerName || 'N/A'}</p>
                        </div>
                        {reportData.cause.details?.missingParams && reportData.cause.details.missingParams.length > 0 && (
                            <div className="border border-slate-800/30 rounded-lg p-4 bg-slate-900/40">
                                <span className="text-sm font-medium text-slate-400">Missing Parameters</span>
                                <div className="flex flex-wrap gap-2 mt-2">
                                    {reportData.cause.details.missingParams.map((param, idx) => (
                                        <span key={idx} className="px-2 py-1 bg-red-900/50 text-red-300 text-xs font-mono rounded border border-red-800">
                      {param}
                    </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="border border-slate-800/30 rounded-lg p-4 bg-slate-900/40">
                            <span className="text-sm font-medium text-slate-400">Problem</span>
                            <p className="text-sm text-slate-300 mt-1">{reportData.aiDescription.slice(0, 120)}{reportData.aiDescription.length > 120 ? '' : ''}</p>
                        </div>
                    </div>
                </div>

                {/* Solutions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-gradient-to-br from-slate-900/50 to-slate-900/30 rounded-xl p-6 border border-slate-800/20 shadow-sm">
                        <h2 className="text-xl font-bold text-white mb-4">AI Recommended Solution</h2>
                        <p className="text-slate-300 leading-relaxed">{reportData.aiSolution}</p>
                    </div>
                    <div className="bg-gradient-to-br from-slate-900/50 to-slate-900/30 rounded-xl p-6 border border-slate-800/20 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-xl font-bold text-white">Human Solution</h2>
                            <div className="text-sm text-slate-300">Executed by: <span className="font-medium text-white">{reportData.humanBy || '—'}</span></div>
                        </div>
                        <p className="text-slate-300 leading-relaxed">{reportData.humanSolution}</p>
                    </div>
                </div>

                {/* Charts */}
                <div>
                    <div className="flex gap-2 mb-4">
                        <button onClick={() => setActiveChart('failed')} className={`px-3 py-1 rounded-md text-sm font-medium ${activeChart === 'failed' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800'}`}>Failed Transactions</button>
                        <button onClick={() => setActiveChart('latency')} className={`px-3 py-1 rounded-md text-sm font-medium ${activeChart === 'latency' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800'}`}>Latency</button>
                        <button onClick={() => setActiveChart('technical')} className={`px-3 py-1 rounded-md text-sm font-medium ${activeChart === 'technical' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800'}`}>Technical Errors</button>
                        <button onClick={() => setActiveChart('approval')} className={`px-3 py-1 rounded-md text-sm font-medium ${activeChart === 'approval' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800'}`}>Approval Distribution</button>
                        <button onClick={() => setActiveChart('success')} className={`px-3 py-1 rounded-md text-sm font-medium ${activeChart === 'success' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800'}`}>Success Rate</button>
                    </div>

                    <div className="bg-gradient-to-b from-slate-900/60 to-slate-900/40 rounded-xl p-6 border border-slate-800/20 shadow-sm">
                        {activeChart === 'failed' && (
                            <>
                                <h2 className="text-xl font-bold text-gray-100 mb-6">Failed Transactions by Hour</h2>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={reportData.failedTransactions}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                        <XAxis dataKey="hour" tick={{ fontSize: 12, fill: '#9ca3af' }} stroke="#6b7280" />
                                        <YAxis tick={{ fill: '#9ca3af' }} stroke="#6b7280" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                                            labelStyle={{ color: '#f3f4f6' }}
                                            itemStyle={{ color: '#e5e7eb' }}
                                        />
                                        <Legend wrapperStyle={{ color: '#9ca3af' }} />
                                        <Bar dataKey="count" fill="#ef4444" name="Failed Transactions" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </>
                        )}

                        {activeChart === 'latency' && (
                            <>
                                <h2 className="text-xl font-bold text-white mb-6">Latency by Hour</h2>
                                <ResponsiveContainer width="100%" height={300}>
                                    <LineChart data={reportData.latency}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                        <XAxis dataKey="hour" tick={{ fontSize: 12, fill: '#9ca3af' }} stroke="#6b7280" />
                                        <YAxis tick={{ fill: '#9ca3af' }} stroke="#6b7280" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                                            labelStyle={{ color: '#f3f4f6' }}
                                            itemStyle={{ color: '#e5e7eb' }}
                                        />
                                        <Legend wrapperStyle={{ color: '#9ca3af' }} />
                                        <Line type="monotone" dataKey="ms" stroke="#3b82f6" strokeWidth={2} name="Latency (ms)" animationDuration={450} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </>
                        )}

                        {activeChart === 'technical' && (
                            <>
                                <h2 className="text-xl font-bold text-white mb-6">Technical Errors by Hour</h2>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={reportData.technicalErrors}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                        <XAxis dataKey="hour" tick={{ fontSize: 12, fill: '#9ca3af' }} stroke="#6b7280" />
                                        <YAxis tick={{ fill: '#9ca3af' }} stroke="#6b7280" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                                            labelStyle={{ color: '#f3f4f6' }}
                                            itemStyle={{ color: '#e5e7eb' }}
                                        />
                                        <Legend wrapperStyle={{ color: '#9ca3af' }} />
                                        <Bar dataKey="400" fill="#f59e0b" name="400 Bad Request" />
                                        <Bar dataKey="500" fill="#ef4444" name="500 Internal Server Error" />
                                        <Bar dataKey="502" fill="#dc2626" name="502 Bad Gateway" />
                                        <Bar dataKey="503" fill="#991b1b" name="503 Service Unavailable" />
                                        <Bar dataKey="504" fill="#7f1d1d" name="504 Gateway Timeout" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </>
                        )}

                        {activeChart === 'approval' && (
                            <>
                                <h2 className="text-xl font-bold text-white mb-6">Approval Status Distribution</h2>
                                <div className="flex items-center justify-center">
                                    <ResponsiveContainer width="100%" height={350}>
                                        <PieChart>
                                            <Pie
                                                data={reportData.approvalDistribution}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                label={({ status, count, percent }) => `${status}: ${count} (${(percent * 100).toFixed(0)}%)`}
                                                outerRadius={100}
                                                fill="#8884d8"
                                                animationDuration={450}
                                                dataKey="count"
                                            >
                                                {reportData.approvalDistribution.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                                                labelStyle={{ color: '#f3f4f6' }}
                                                itemStyle={{ color: '#e5e7eb' }}
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                            </>
                        )}

                        {activeChart === 'success' && (
                            <>
                                <h2 className="text-xl font-bold text-white mb-6">Transaction Success Rate by Hour</h2>
                                <ResponsiveContainer width="100%" height={350}>
                                    <LineChart data={reportData.successRate}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                        <XAxis dataKey="hour" tick={{ fontSize: 12, fill: '#9ca3af' }} stroke="#6b7280" />
                                        <YAxis
                                            domain={[0, 100]}
                                            tick={{ fill: '#9ca3af' }}
                                            stroke="#6b7280"
                                            label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                                        />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                                            labelStyle={{ color: '#f3f4f6' }}
                                            itemStyle={{ color: '#e5e7eb' }}
                                            formatter={(value: number) => `${value.toFixed(1)}%`}
                                        />
                                        <Legend wrapperStyle={{ color: '#9ca3af' }} />
                                        <Line
                                            type="monotone"
                                            dataKey="rate"
                                            stroke="#10b981"
                                            strokeWidth={3}
                                            animationDuration={450}
                                            name="Success Rate (%)"
                                            dot={{ fill: '#10b981', r: 4 }}
                                            activeDot={{ r: 6 }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TransactionReport;