import { useParams } from 'react-router-dom';
import TransactionReport from "@/components/ReportData";

export const ReportPage = () => {
    const { transactionId } = useParams<{ transactionId: string }>();

    // TODO: Use transactionId to fetch report data from API
    // Example: const { data, loading } = useFetchReport(transactionId);
    // For now, transactionId is available but not used until API integration
    console.log('Report ID:', transactionId);

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Report component - transactionId will be used to fetch data */}
            <TransactionReport />
        </div>
    );
};
