import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import TransactionReport from "@/components/ReportData";
import apiBackClient from '@/services/apiBackClient';
import { API_ENDPOINTS } from '@/constants/reports';

export const ReportPage = () => {
    const { transactionId } = useParams<{ transactionId: string }>();
    const [report, setReport] = useState<any | null>(null);

    useEffect(() => {
        if (!transactionId) return;
        const fetchReport = async () => {
            try {
                const resp = await apiBackClient.get(API_ENDPOINTS.REPORT_BY_ID(encodeURIComponent(transactionId)));
                console.debug('single report response:', resp.data);
                // backend may return object inside data or items
                const possible = resp.data;
                const obj = possible?.report || possible?.result || possible?.data || possible || null;
                setReport(obj);
            } catch (err) {
                console.error('Error fetching single report', err);
            }
        };
        fetchReport();
    }, [transactionId]);

    return (
        <div className="container mx-auto px-4 py-8">
            <TransactionReport initialData={report} />
        </div>
    );
};
