export interface Report {
    transactionId: string;
    merchant: string;
    provider: string;
    title: string;
    status: 'pending' | 'in-progress' | 'resolved' | 'rejected';
    date: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    affectedTransactions: number;
}

export interface ReportFilters {
    merchant: string;
    providers: string[]; // Changed to array for multiple selection
}

// API response types for future integration
export interface MerchantProvider {
    merchantId: string;
    merchantName: string;
    providers: string[];
}

export interface ApiMerchantsResponse {
    merchants: string[];
}

export interface ApiProvidersResponse {
    providers: string[];
}
