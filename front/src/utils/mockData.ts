import type { Report } from '@/types/report';

/**
 * Generates mock reports for development and testing purposes
 * @param count - Number of reports to generate (default: 50)
 * @returns Array of mock Report objects
 */
export const generateMockReports = (count: number = 50): Report[] => {
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
  const statuses: Array<'pending' | 'in-progress' | 'resolved' | 'rejected'> = 
    ['pending', 'in-progress', 'resolved', 'rejected'];
  const severities: Array<'low' | 'medium' | 'high' | 'critical'> = 
    ['low', 'medium', 'high', 'critical'];

  const reports: Report[] = [];
  const now = Date.now();
  const thirtyDaysInMs = 30 * 24 * 60 * 60 * 1000;

  for (let i = 0; i < count; i++) {
    const randomDate = new Date(now - Math.random() * thirtyDaysInMs);

    reports.push({
      transactionId: `TXN-${now}-${i.toString().padStart(4, '0')}`,
      merchant: merchants[Math.floor(Math.random() * merchants.length)],
      provider: providers[Math.floor(Math.random() * providers.length)],
      title: titles[Math.floor(Math.random() * titles.length)],
      status: statuses[Math.floor(Math.random() * statuses.length)],
      date: randomDate.toISOString(),
      severity: severities[Math.floor(Math.random() * severities.length)],
      affectedTransactions: Math.floor(Math.random() * 5000) + 100
    });
  }

  // Sort by date (most recent first)
  return reports.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
};

/**
 * Extract unique values from an array of objects
 * @param items - Array of items
 * @param key - Key to extract
 * @returns Sorted array of unique values
 */
export const getUniqueValues = <T extends Record<string, any>>(
  items: T[],
  key: keyof T
): string[] => {
  return Array.from(new Set(items.map(item => String(item[key])))).sort();
};
