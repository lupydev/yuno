import React, { useState } from 'react';
import { ArrowRight, Globe, CreditCard, Settings, LayoutDashboard, Activity } from 'lucide-react';
export const DashboardClient = () => {
    return (
        <div className="flex md:flex-row h-screen w-full items-center justify-center">
            {/*
 
 const navItems = [
        { icon: LayoutDashboard, label: 'Overview', active: true },
        { icon: Activity, label: 'Transactions', active: false },
        { icon: Globe, label: 'Countries', active: false },
        { icon: CreditCard, label: 'Providers', active: false },
        { icon: Settings, label: 'Settings', active: false }
    ];
 принципал
 const incidents = [
        { id: 1, severity: 'high', title: 'Stripe declining 15% more cards than usual', impact: '~240 transactions/hour affected', time: '2 hours ago' },
        { id: 2, severity: 'medium', title: 'PayPal response times slower in EU', impact: '~80 transactions/hour affected', time: '45 minutes ago' }
    ];

    const countryData = [
        { country: 'United States', rate: 96.2, volume: 5840, change: 0.3 },
        { country: 'United Kingdom', rate: 93.1, volume: 2340, change: -3.2 },
        { country: 'Germany', rate: 91.5, volume: 1890, change: -4.1 },
        { country: 'France', rate: 95.8, volume: 1520, change: 1.2 },
        { country: 'Spain', rate: 94.2, volume: 980, change: -0.8 },
        { country: 'Italy', rate: 96.5, volume: 760, change: 2.1 }
    ];

    const providerData = [
        { provider: 'Stripe', rate: 93.8, volume: 8200, change: -2.8, status: 'warning' },
        { provider: 'PayPal', rate: 95.2, volume: 3100, change: -0.5, status: 'good' },
        { provider: 'Adyen', rate: 96.1, volume: 1547, change: 0.8, status: 'good' }
    ];

    // Transaction-level data
    const transactionData = [
        { merchant: 'Shopito', provider: 'Stripe', method: 'Tarjeta', country: 'MX', result: 'Approved' },
        { merchant: 'Shopito', provider: 'Stripe', method: 'Tarjeta', country: 'MX', result: 'Declined' },
        { merchant: 'StoreX', provider: 'Adyen', method: 'PSE', country: 'CO', result: 'Declined' },
        { merchant: 'Shopito', provider: 'BAC', method: 'Tarjeta', country: 'CO', result: 'Declined' },
        { merchant: 'Shopito', provider: 'Stripe', method: 'Tarjeta', country: 'MX', result: 'Declined' },
        { merchant: 'StoreX', provider: 'Stripe', method: 'Tarjeta', country: 'US', result: 'Approved' },
        { merchant: 'Shopito', provider: 'PayPal', method: 'Wallet', country: 'MX', result: 'Approved' },
        { merchant: 'MegaShop', provider: 'Adyen', method: 'Tarjeta', country: 'CO', result: 'Declined' },
        { merchant: 'Shopito', provider: 'Stripe', method: 'Tarjeta', country: 'MX', result: 'Approved' },
        { merchant: 'StoreX', provider: 'BAC', method: 'PSE', country: 'CO', result: 'Declined' },
        { merchant: 'MegaShop', provider: 'Stripe', method: 'Tarjeta', country: 'US', result: 'Approved' },
        { merchant: 'Shopito', provider: 'Adyen', method: 'Tarjeta', country: 'MX', result: 'Declined' },
        { merchant: 'StoreX', provider: 'PayPal', method: 'Wallet', country: 'US', result: 'Approved' },
        { merchant: 'Shopito', provider: 'Stripe', method: 'PSE', country: 'CO', result: 'Declined' },
        { merchant: 'MegaShop', provider: 'BAC', method: 'Tarjeta', country: 'CO', result: 'Approved' },
    ];

    const [selectedMerchant, setSelectedMerchant] = useState('Shopito');

    // Get unique merchants
    const merchants = [...new Set(transactionData.map(t => t.merchant))];

    // Count issues by dimension (only declined)
    const countByDimension = (dimension) => {
        const counts = {};
        transactionData
            .filter(t => t.result === 'Declined')
            .forEach(t => {
                counts[t[dimension]] = (counts[t[dimension]] || 0) + 1;
            });
        return Object.entries(counts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5); // Top 5
    };
    const issuesByDimension = {
        merchant: countByDimension('merchant'),
        provider: countByDimension('provider'),
        method: countByDimension('method'),
        country: countByDimension('country')
    };

    // Filter by selected merchant
    const merchantFiltered = transactionData.filter(t => t.merchant === selectedMerchant && t.result === 'Declined');
    const providerIssues = {};
    merchantFiltered.forEach(t => {
        providerIssues[t.provider] = (providerIssues[t.provider] || 0) + 1;
    });
    const providerIssuesArray = Object.entries(providerIssues).sort((a, b) => b[1] - a[1]);

    const recommendations = [
        { priority: 'high', action: 'Switch UK traffic to backup provider', reason: 'Stripe UK success rate dropped 4% in last 2 hours', impact: 'Could recover ~120 transactions/hour' },
        { priority: 'medium', action: 'Review card decline messages', reason: 'Customers seeing unclear error messages', impact: 'May improve retry rate' }
    ];

                    {/* Active Incidents *}
                    <div className="grid grid-cols-1 gap-6 mb-6">
                        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                            <div className="p-5 border-b border-slate-800">
                                <h3 className="text-lg font-bold text-white">Active Issues</h3>
                                <p className="text-slate-400 text-sm mt-1">Problems affecting payments right now</p>
                            </div>
                            <div className="grid grid-cols-2 divide-x divide-slate-800">
                                {incidents.map(incident => (
                                    <div key={incident.id} className="p-5 hover:bg-slate-800/50 transition-colors">
                                        <div className="flex items-start gap-3 mb-2">
                                            <div className={`w-2 h-2 rounded-full mt-1.5 ${incident.severity === 'high' ? 'bg-red-500' : 'bg-amber-500'}`} />
                                            <div className="flex-1">
                                                <h4 className="font-semibold text-white text-sm leading-tight">{incident.title}</h4>
                                            </div>
                                        </div>
                                        <p className="text-slate-400 text-xs ml-5">{incident.impact}</p>
                                        <span className="text-xs text-slate-500 ml-5">{incident.time}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Issues by Dimension *}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
                        <h3 className="text-lg font-bold text-white mb-1">Issues by Category</h3>
                        <p className="text-slate-400 text-sm mb-6">Declined transactions breakdown across dimensions</p>

                        <div className="grid grid-cols-4 gap-6">
                            {/* Merchant *}
                            <div>
                                <h4 className="text-sm font-semibold text-slate-300 mb-4">Merchant</h4>
                                <div className="space-y-3">
                                    {issuesByDimension.merchant.map(([name, count], idx) => (
                                        <div key={idx} className="space-y-1">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm text-white">{name}</span>
                                                <span className="text-sm font-bold text-white">{count}</span>
                                            </div>
                                            <div className="bg-slate-800 rounded-full h-2">
                                                <div
                                                    className="bg-blue-500 h-2 rounded-full transition-all"
                                                    style={{ width: `${(count / Math.max(...issuesByDimension.merchant.map(i => i[1]))) * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Provider *}
                            <div>
                                <h4 className="text-sm font-semibold text-slate-300 mb-4">Provider</h4>
                                <div className="space-y-3">
                                    {issuesByDimension.provider.map(([name, count], idx) => (
                                        <div key={idx} className="space-y-1">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm text-white">{name}</span>
                                                <span className="text-sm font-bold text-white">{count}</span>
                                            </div>
                                            <div className="bg-slate-800 rounded-full h-2">
                                                <div
                                                    className="bg-purple-500 h-2 rounded-full transition-all"
                                                    style={{ width: `${(count / Math.max(...issuesByDimension.provider.map(i => i[1]))) * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Method *}
                            <div>
                                <h4 className="text-sm font-semibold text-slate-300 mb-4">Método</h4>
                                <div className="space-y-3">
                                    {issuesByDimension.method.map(([name, count], idx) => (
                                        <div key={idx} className="space-y-1">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm text-white">{name}</span>
                                                <span className="text-sm font-bold text-white">{count}</span>
                                            </div>
                                            <div className="bg-slate-800 rounded-full h-2">
                                                <div
                                                    className="bg-pink-500 h-2 rounded-full transition-all"
                                                    style={{ width: `${(count / Math.max(...issuesByDimension.method.map(i => i[1]))) * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Country *}
                            <div>
                                <h4 className="text-sm font-semibold text-slate-300 mb-4">País</h4>
                                <div className="space-y-3">
                                    {issuesByDimension.country.map(([name, count], idx) => (
                                        <div key={idx} className="space-y-1">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm text-white">{name}</span>
                                                <span className="text-sm font-bold text-white">{count}</span>
                                            </div>
                                            <div className="bg-slate-800 rounded-full h-2">
                                                <div
                                                    className="bg-cyan-500 h-2 rounded-full transition-all"
                                                    style={{ width: `${(count / Math.max(...issuesByDimension.country.map(i => i[1]))) * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Provider Issues by Merchant *}
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h3 className="text-lg font-bold text-white mb-1">Provider Issues by Merchant</h3>
                                <p className="text-slate-400 text-sm">Select a merchant to see provider-specific problems</p>
                            </div>
                            <select
                                value={selectedMerchant}
                                onChange={(e) => setSelectedMerchant(e.target.value)}
                                className="px-4 py-2 border border-slate-700 rounded-lg bg-slate-800 text-slate-200 font-medium"
                            >
                                {merchants.map(m => (
                                    <option key={m} value={m}>{m}</option>
                                ))}
                            </select>
                        </div>

                        {providerIssuesArray.length > 0 ? (
                            <div className="grid grid-cols-5 gap-4">
                                {providerIssuesArray.map(([provider, count], idx) => (
                                    <div key={idx} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                                        <div className="text-center">
                                            <div className="text-3xl font-bold text-white mb-2">{count}</div>
                                            <div className="text-sm text-slate-300 font-medium">{provider}</div>
                                            <div className="mt-3 bg-slate-800 rounded-full h-2">
                                                <div
                                                    className="bg-purple-500 h-2 rounded-full transition-all"
                                                    style={{ width: `${(count / Math.max(...providerIssuesArray.map(i => i[1]))) * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-12 text-slate-400">
                                No declined transactions for {selectedMerchant}
                            </div>
                        )}
                    </div>

                    {/* Country & Provider Performance + Recommendations *}
                    <div className="grid grid-cols-3 gap-6 mb-6">

                        {/* Country Breakdown *}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                            <h3 className="text-lg font-bold text-white mb-1">By Country</h3>
                            <p className="text-slate-400 text-sm mb-5">Success rates by location</p>
                            <div className="space-y-3">
                                {countryData.map((country, idx) => (
                                    <div key={idx} className="space-y-1.5">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-white">{country.country}</span>
                                            <div className="text-right">
                                                <div className="text-sm font-bold text-white">{country.rate}%</div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 bg-slate-800 rounded-full h-1.5">
                                                <div
                                                    className={`h-1.5 rounded-full ${country.rate >= 95 ? 'bg-emerald-500' : country.rate >= 92 ? 'bg-amber-500' : 'bg-red-500'}`}
                                                    style={{ width: `${country.rate}%` }}
                                                />
                                            </div>
                                            <span className={`text-xs font-medium ${country.change < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                        {country.change > 0 ? '+' : ''}{country.change}%
                      </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Provider Breakdown *}
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                            <h3 className="text-lg font-bold text-white mb-1">By Provider</h3>
                            <p className="text-slate-400 text-sm mb-5">Payment processor performance</p>
                            <div className="space-y-5">
                                {providerData.map((provider, idx) => (
                                    <div key={idx} className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-white">{provider.provider}</span>
                                            <div className="text-right">
                                                <div className="text-sm font-bold text-white">{provider.rate}%</div>
                                                <div className="text-xs text-slate-500">{provider.volume.toLocaleString()} txns</div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 bg-slate-800 rounded-full h-2">
                                                <div
                                                    className={`h-2 rounded-full ${provider.status === 'good' ? 'bg-emerald-500' : 'bg-amber-500'}`}
                                                    style={{ width: `${provider.rate}%` }}
                                                />
                                            </div>
                                            <span className={`text-xs font-medium ${provider.change < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                        {provider.change > 0 ? '+' : ''}{provider.change}%
                      </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Recommendations *}
                        <div className="bg-gradient-to-br from-blue-500/10 to-indigo-500/10 border-2 border-blue-500/30 rounded-xl p-6">
                            <h3 className="text-lg font-bold text-white mb-1">Actions</h3>
                            <p className="text-slate-400 text-sm mb-5">Steps to improve performance</p>
                            <div className="space-y-3">
                                {recommendations.map((rec, idx) => (
                                    <div key={idx} className="bg-slate-900/50 rounded-lg p-4 border border-blue-500/20">
                                        <div className="flex items-start gap-3">
                                            <div className={`w-2 h-2 rounded-full mt-1.5 ${rec.priority === 'high' ? 'bg-red-500' : 'bg-amber-500'}`} />
                                            <div className="flex-1">
                                                <h4 className="font-bold text-white text-sm mb-1">{rec.action}</h4>
                                                <p className="text-slate-400 text-xs mb-2">{rec.reason}</p>
                                                <p className="text-xs text-blue-400 font-medium">{rec.impact}</p>
                                            </div>
                                        </div>
                                        <button className="mt-3 w-full px-3 py-2 bg-blue-600 text-white text-xs rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2">
                                            Take Action
                                            <ArrowRight className="w-3 h-3" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
            */}
        </div>
    );
};