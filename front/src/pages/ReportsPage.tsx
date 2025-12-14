import React, { useState, useMemo } from 'react';
import { ReportFilters, ReportsTable } from '@/components/reports';
import { Pagination } from '@/components/Pagination';
import type { Report, ReportFilters as ReportFiltersType } from '@/types/report';
import { FileText } from 'lucide-react';

// TODO: Replace with actual API calls
// import { fetchMerchants, fetchProvidersByMerchant, fetchReports } from '@/services/apiBackClient';

// Mock data - simulating backend reports
const generateMockReports = (): Report[] => {
    const merchants = ['McDonald\'s', 'Starbucks', 'Burger King', 'Walmart', 'Amazon', 'Nike'];
    const providers = ['PayU', 'Stripe', 'Adyen', 'Mercado Pago', 'PayPal'];
    const titles = [
        'Payment Gateway Timeout Issue',
        'High Rate of Failed Transactions',
        'Provider Integration Error',
        'Missing Parameters in Request',
        'Authentication Failure Pattern',
        'Unusual Latency Spike',
        'Circuit Breaker Triggered',
        'Rate Limit Exceeded',
        'Database Connection Timeout',
        'Invalid Response Format'
    ];
    const statuses: Array<'pending' | 'in-progress' | 'resolved' | 'rejected'> = ['pending', 'in-progress', 'resolved', 'rejected'];
    const severities: Array<'low' | 'medium' | 'high' | 'critical'> = ['low', 'medium', 'high', 'critical'];

    const reports: Report[] = [];
    const now = new Date();

    for (let i = 0; i < 50; i++) {
        const merchant = merchants[Math.floor(Math.random() * merchants.length)];
        const provider = providers[Math.floor(Math.random() * providers.length)];
        const date = new Date(now.getTime() - Math.random() * 30 * 24 * 60 * 60 * 1000); // Last 30 days

        reports.push({
            transactionId: `TXN-${Date.now()}-${i.toString().padStart(4, '0')}`,
            merchant,
            provider,
            title: titles[Math.floor(Math.random() * titles.length)],
            status: statuses[Math.floor(Math.random() * statuses.length)],
            date: date.toISOString(),
            severity: severities[Math.floor(Math.random() * severities.length)],
            affectedTransactions: Math.floor(Math.random() * 5000) + 100
        });
    }

    // Sort by date (most recent first)
    return reports.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
};

const ITEMS_PER_PAGE = 10;

export const ReportsPage = () => {
    const [mockReports] = useState<Report[]>(generateMockReports());
    const [filters, setFilters] = useState<ReportFiltersType>({
        merchant: '',
        providers: []
    });
    const [currentPage, setCurrentPage] = useState(0);

    // TODO: Fetch merchants from API on component mount
    // useEffect(() => {
    //     const loadMerchants = async () => {
    //         const data = await fetchMerchants();
    //         setMerchants(data.merchants);
    //     };
    //     loadMerchants();
    // }, []);

    // TODO: Fetch providers when merchant changes
    // useEffect(() => {
    //     if (filters.merchant) {
    //         const loadProviders = async () => {
    //             const data = await fetchProvidersByMerchant(filters.merchant);
    //             setProviders(data.providers);
    //         };
    //         loadProviders();
    //     } else {
    //         // Load all providers if no merchant selected
    //         const loadAllProviders = async () => {
    //             const data = await fetchAllProviders();
    //             setProviders(data.providers);
    //         };
    //         loadAllProviders();
    //     }
    // }, [filters.merchant]);

    // Get unique merchants and providers for filters (mock data)
    const merchants = useMemo(() => {
        return Array.from(new Set(mockReports.map(r => r.merchant))).sort();
    }, [mockReports]);

    const providers = useMemo(() => {
        // TODO: When merchant is selected, filter providers by merchant
        // For now, show all providers
        return Array.from(new Set(mockReports.map(r => r.provider))).sort();
    }, [mockReports]);

    // Filter reports based on filters
    const filteredReports = useMemo(() => {
        return mockReports.filter(report => {
            if (filters.merchant && report.merchant !== filters.merchant) {
                return false;
            }
            if (filters.providers.length > 0 && !filters.providers.includes(report.provider)) {
                return false;
            }
            return true;
        });
    }, [mockReports, filters]);

    // Paginate filtered reports
    const paginatedReports = useMemo(() => {
        const startIndex = currentPage * ITEMS_PER_PAGE;
        return filteredReports.slice(startIndex, startIndex + ITEMS_PER_PAGE);
    }, [filteredReports, currentPage]);

    const totalPages = Math.ceil(filteredReports.length / ITEMS_PER_PAGE);

    const handleFilterChange = (key: string, value: string | string[]) => {
        setFilters(prev => ({ ...prev, [key]: value }));
        setCurrentPage(0); // Reset to first page when filters change
    };

    const handleClearFilters = () => {
        setFilters({ merchant: '', providers: [] });
        setCurrentPage(0);
    };

    const handlePageChange = (page: number) => {
        setCurrentPage(page);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="mb-6">
                <div className="flex items-center gap-3 mb-2">
                    <FileText size={32} className="text-blue-600" />
                    <h1 className="text-3xl font-bold text-gray-900">Alert Reports</h1>
                </div>
                <p className="text-gray-600">
                    Manage and review reports generated by the alert system
                </p>
            </div>

            {/* Filters */}
            <ReportFilters
                filters={filters}
                onFilterChange={handleFilterChange}
                onClearFilters={handleClearFilters}
                merchants={merchants}
                providers={providers}
            />

            {/* Results count */}
            <div className="mb-4 text-sm text-gray-600">
                Showing {paginatedReports.length} of {filteredReports.length} reports
            </div>

            {/* Reports Table */}
            <ReportsTable reports={paginatedReports} />

            {/* Pagination */}
            {totalPages > 1 && (
                <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
                />
            )}
        </div>
    );
};
