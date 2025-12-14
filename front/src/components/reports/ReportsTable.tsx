import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle, Clock, XCircle, TrendingUp } from 'lucide-react';
import type { Report } from '@/types/report';

interface ReportsTableProps {
    reports: Report[];
}

export const ReportsTable: React.FC<ReportsTableProps> = ({ reports }) => {
    const navigate = useNavigate();

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
                return <AlertCircle size={18} className="text-gray-500" />;
        }
    };

    const getStatusText = (status: string) => {
        switch (status) {
            case 'resolved':
                return 'Resolved';
            case 'in-progress':
                return 'In Progress';
            case 'rejected':
                return 'Rejected';
            case 'pending':
            default:
                return 'Pending';
        }
    };

    const getSeverityBadge = (severity: string) => {
        const classes = {
            low: 'bg-blue-100 text-blue-800',
            medium: 'bg-yellow-100 text-yellow-800',
            high: 'bg-orange-100 text-orange-800',
            critical: 'bg-red-100 text-red-800'
        };

        const labels = {
            low: 'Low',
            medium: 'Medium',
            high: 'High',
            critical: 'Critical'
        };

        return (
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${classes[severity as keyof typeof classes]}`}>
                {labels[severity as keyof typeof labels]}
            </span>
        );
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('en-US', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    };

    const handleRowClick = (transactionId: string) => {
        navigate(`/report/${transactionId}`);
    };

    if (reports.length === 0) {
        return (
            <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">No reports found</p>
                <p className="text-gray-400 text-sm mt-2">Try adjusting the filters</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Transaction ID
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Title
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Merchant
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Provider
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Severity
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Status
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Transactions
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Date
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {reports.map((report) => (
                            <tr
                                key={report.transactionId}
                                onClick={() => handleRowClick(report.transactionId)}
                                className="hover:bg-gray-50 cursor-pointer transition-colors"
                            >
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-blue-600">
                                    {report.transactionId}
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                                    {report.title}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                    {report.merchant}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                    {report.provider}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                    {getSeverityBadge(report.severity)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center gap-2">
                                        {getStatusIcon(report.status)}
                                        <span className="text-sm text-gray-700">
                                            {getStatusText(report.status)}
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                    <div className="flex items-center gap-1">
                                        <TrendingUp size={14} className="text-red-500" />
                                        {report.affectedTransactions.toLocaleString()}
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
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
