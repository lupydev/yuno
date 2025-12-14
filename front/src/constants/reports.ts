// Report status constants
export const REPORT_STATUSES = {
  PENDING: 'pending',
  IN_PROGRESS: 'in-progress',
  RESOLVED: 'resolved',
  REJECTED: 'rejected',
} as const;

export type ReportStatus = typeof REPORT_STATUSES[keyof typeof REPORT_STATUSES];

// Report severity constants
export const REPORT_SEVERITIES = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical',
} as const;

export type ReportSeverity = typeof REPORT_SEVERITIES[keyof typeof REPORT_SEVERITIES];

// Pagination constants
export const PAGINATION = {
  ITEMS_PER_PAGE: 10,
  MAX_VISIBLE_PAGES: 7,
} as const;

// UI Messages
export const UI_MESSAGES = {
  REPORTS: {
    NO_REPORTS_FOUND: 'No reports found',
    TRY_ADJUSTING_FILTERS: 'Try adjusting the filters',
    SHOWING_RESULTS: (current: number, total: number) => `Showing ${current} of ${total} reports`,
  },
  FILTERS: {
    ALL_MERCHANTS: 'All Merchants',
    ALL_PROVIDERS: 'All Providers',
    PROVIDERS_SELECTED: (count: number) => `${count} Providers Selected`,
    CLEAR_FILTERS: 'Clear Filters',
  },
  STATUS: {
    PENDING: 'Pending',
    IN_PROGRESS: 'In Progress',
    RESOLVED: 'Resolved',
    REJECTED: 'Rejected',
  },
  SEVERITY: {
    LOW: 'Low',
    MEDIUM: 'Medium',
    HIGH: 'High',
    CRITICAL: 'Critical',
  },
} as const;

// API endpoints
export const API_ENDPOINTS = {
  REPORTS: '/reports',
  MERCHANTS: '/merchants',
  PROVIDERS: '/providers',
  PROVIDERS_BY_MERCHANT: (merchantId: string) => `/merchants/${merchantId}/providers`,
  REPORT_BY_ID: (transactionId: string) => `/reports/${transactionId}`,
} as const;

// Date format options
export const DATE_FORMAT_OPTIONS: Intl.DateTimeFormatOptions = {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
} as const;
