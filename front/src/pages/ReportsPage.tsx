import { useState, useMemo, useEffect } from 'react';
import { ReportFilters, ReportsTable } from '@/components/reports';
import { Pagination } from '@/components/Pagination';
import { FileText } from 'lucide-react';
import { useReports } from '@/hooks/useReports';
import apiBackClient from '@/services/apiBackClient';
import { API_ENDPOINTS, UI_MESSAGES } from '@/constants/reports';
import { getUniqueValues } from '@/utils/mockData';
import { scrollToTop } from '@/utils/formatters';

// TODO: Replace with actual API calls
// import { fetchReports, fetchMerchants, fetchProvidersByMerchant } from '@/services/reportService';

export const ReportsPage = () => {
    const [reports, setReports] = useState<any[]>([]);
    const [merchants, setMerchants] = useState<string[]>([]);
    const [providers, setProviders] = useState<string[]>([]);

    const {
        filteredReports,
        paginatedReports,
        currentPage,
        totalPages,
        filters,
        handleFilterChange,
        handleClearFilters,
        handlePageChange,
    } = useReports(reports);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Build query params based on filters (client-side selection)
                const params = new URLSearchParams();
                if (filters.merchant) params.append('merchant', filters.merchant);
                if (filters.providers && filters.providers.length > 0) params.append('provider', filters.providers.join(','));

                const resp = await apiBackClient.get(`${API_ENDPOINTS.REPORTS}?${params.toString()}`);
                console.debug('reports fetch response:', resp.data);
                // handle multiple possible response shapes
                const possible = resp.data;
                const arr = Array.isArray(possible)
                    ? possible
                    : possible?.alert_reports || possible?.reports || possible?.results || possible?.items || possible?.data || [];

                // Map backend report shape to frontend Report interface
                const mapped = (arr || []).map((it: any) => {
                    const mapStatus = (s: string | undefined) => {
                        if (!s) return 'pending';
                        const lower = s.toLowerCase();
                        if (lower === 'failed' || lower === 'error' || lower === 'rejected') return 'rejected';
                        if (lower === 'pending' || lower === 'processing') return 'pending';
                        if (lower === 'success' || lower === 'approved' || lower === 'resolved') return 'resolved';
                        return 'pending';
                    };

                    return {
                        transactionId: it.id || it.transaction_id || it.provider_transaction_id || it.normalized_event_id || 'unknown',
                        merchant: it.merchant || it.merchant_name || it.merchantName || it.raw_data?.merchant || 'Unknown',
                        provider: it.provider || it.provider_name || it.raw_data?.provider || 'Unknown',
                        title: it.title || (it.ai_explanation ? it.ai_explanation.slice(0, 80) : 'Report'),
                        status: mapStatus(it.status_category || it.status || it.provider_status),
                        date: it.date || it.event_created_at || it.created_at || new Date().toISOString(),
                        severity: (it.severity || 'low').toLowerCase(),
                        affectedTransactions: it.transactions || it.transactions_count || it.affected || 1,
                        // keep original payload for detail pages
                        __raw: it,
                    };
                });

                setReports(mapped);
            } catch (err) {
                console.error('Error fetching reports', err);
            }

            try {
                const m = await apiBackClient.get(API_ENDPOINTS.MERCHANTS);
                console.debug('merchants fetch response:', m.data);
                const md = m.data;
                let merchantsArr = Array.isArray(md) ? md : md?.merchants || md?.results || md?.items || md?.data || [];
                // normalize to string names
                merchantsArr = merchantsArr.map ? merchantsArr.map((m: any) => m?.merchant_name || m?.name || m?.merchant || (typeof m === 'string' ? m : JSON.stringify(m))) : [];
                setMerchants(merchantsArr);
            } catch (err) {
                console.error('Error fetching merchants', err);
            }

            try {
                // If merchant selected, fetch providers specific to merchant
                if (filters.merchant) {
                    try {
                        const pm = await apiBackClient.get(API_ENDPOINTS.PROVIDERS_BY_MERCHANT(encodeURIComponent(filters.merchant)));
                        console.debug('providers-by-merchant fetch response:', pm.data);
                        const pd = pm.data;
                        let providersArr = Array.isArray(pd) ? pd : pd?.providers || pd?.results || pd?.items || pd?.data || [];
                        providersArr = providersArr.map ? providersArr.map((x: any) => x?.provider || x?.name || (typeof x === 'string' ? x : JSON.stringify(x))) : [];
                        setProviders(providersArr);
                    } catch (e) {
                        // fallback to full providers list
                        const p = await apiBackClient.get(API_ENDPOINTS.PROVIDERS);
                        const pd = p.data;
                        let providersArr = Array.isArray(pd) ? pd : pd?.providers || pd?.results || pd?.items || pd?.data || [];
                        providersArr = providersArr.map ? providersArr.map((x: any) => x?.provider || x?.name || (typeof x === 'string' ? x : JSON.stringify(x))) : [];
                        setProviders(providersArr);
                    }
                } else {
                    const p = await apiBackClient.get(API_ENDPOINTS.PROVIDERS);
                    const pd = p.data;
                    let providersArr = Array.isArray(pd) ? pd : pd?.providers || pd?.results || pd?.items || pd?.data || [];
                    providersArr = providersArr.map ? providersArr.map((x: any) => x?.provider || x?.name || (typeof x === 'string' ? x : JSON.stringify(x))) : [];
                    setProviders(providersArr);
                }
            } catch (err) {
                console.error('Error fetching providers', err);
            }
        };
        fetchData();
    }, [filters]);

    const handlePageChangeWithScroll = (page: number) => {
        handlePageChange(page);
        scrollToTop();
    };

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="mb-6">
                <div className="flex items-center gap-3 mb-2">
                    <FileText size={32} className="text-blue-600" />
                    <h1 className="text-3xl font-bold text-white">Alert Reports</h1>
                </div>
                <p className="text-slate-400">
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
            <div className="mb-4 text-sm text-slate-400">
                {UI_MESSAGES.REPORTS.SHOWING_RESULTS(
                    paginatedReports.length,
                    filteredReports.length
                )}
            </div>

            {/* Reports Table */}
            <ReportsTable reports={paginatedReports} />

            {/* Pagination */}
            {totalPages > 1 && (
                <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChangeWithScroll}
                />
            )}
        </div>
    );
};
