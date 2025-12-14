import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle, Clock, XCircle, TrendingUp } from 'lucide-react';
import type { Report } from '@/types/report';
import { getSeverityConfig, getStatusText } from './reportConfig';
import { formatDate, formatNumber } from '@/utils/formatters';
import { UI_MESSAGES } from '@/constants/reports';

interface ReportsTableProps {
    reports: Report[];
}

export const ReportsTable: React.FC<ReportsTableProps> = ({ reports }) => {
    const navigate = useNavigate();
    const [copiedId, setCopiedId] = useState<string>('');

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'resolved':
                return <CheckCircle size={18} className="text-green-500" />;
            case 'in-progress':
                return <Clock size={18} className="text-yellow-500" />;
            case 'rejected':
                return <XCircle size={18} className="text-red-500" />;
            case 'pending':
            default:
                return <AlertCircle size={18} className="text-slate-500" />;
        }
    };

    const getSeverityBadge = (severity: string) => {
        const config = getSeverityConfig(severity);
        return (
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.className}`}>
                {config.label}
            </span>
        );
    };

    const handleRowClick = (transactionId: string) => {
        navigate(`/report/${transactionId}`);
    };

    if (reports.length === 0) {
        return (
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-12 text-center">
                <AlertCircle size={48} className="text-slate-600 mx-auto mb-4" />
                <p className="text-slate-300 text-lg">{UI_MESSAGES.REPORTS.NO_REPORTS_FOUND}</p>
                <p className="text-slate-400 text-sm mt-2">{UI_MESSAGES.REPORTS.TRY_ADJUSTING_FILTERS}</p>
            </div>
        );
    }

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full table-fixed">
                    <thead className="bg-slate-800/50 border-b border-slate-800">
                        <tr>
                            <th className="px-6 py-3 w-36 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                Transaction ID
                            </th>
                            <th className="px-6 py-3 w-1/3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                Title
                            </th>
                            <th className="px-6 py-3 w-1/6 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                Merchant
                            </th>
                            <th className="px-6 py-3 w-1/6 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                Provider
                            </th>
                            <th className="px-6 py-3 w-24 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                Severity
                            </th>
                            <th className="px-6 py-3 w-28 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                Status
                            </th>
                            <th className="px-6 py-3 w-28 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                Transactions
                            </th>
                            <th className="px-6 py-3 w-32 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                Date
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {reports.map((report) => (
                            <tr
                                key={report.transactionId}
                                onClick={() => handleRowClick(report.transactionId)}
                                className="hover:bg-slate-800/30 cursor-pointer transition-colors"
                            >
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); navigator.clipboard && navigator.clipboard.writeText(report.transactionId); setCopiedId(report.transactionId); setTimeout(() => setCopiedId(''), 2000); }}
                                            title={report.transactionId}
                                            className="font-mono text-slate-400 hover:text-slate-200 focus:outline-none"
                                            aria-label={`Copy transaction id ${report.transactionId}`}
                                        >
                                            {report.transactionId && report.transactionId.length > 12 ? `${report.transactionId.slice(0,8)}...${report.transactionId.slice(-4)}` : report.transactionId}
                                        </button>
                                        {copiedId === report.transactionId && (
                                            <span className="text-xs text-emerald-400">Copied</span>
                                        )}
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-sm text-white max-w-xs truncate">
                                    {report.title}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                                    {report.merchant}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                                    {report.provider}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                    {getSeverityBadge(report.severity)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center gap-2">
                                        {getStatusIcon(report.status)}
                                        <span className="text-sm text-slate-300">
                                            {getStatusText(report.status)}
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                                    <div className="flex items-center gap-1">
                                        <TrendingUp size={14} className="text-red-500" />
                                        {formatNumber(report.affectedTransactions)}
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
                                    {formatDate(report.date)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
