import type { Report, ReportFilters } from '@/types/report';

/**
 * Filters reports based on merchant and providers
 * @param reports - Array of reports to filter
 * @param filters - Filter criteria
 * @returns Filtered array of reports
 */
export const filterReports = (reports: Report[], filters: ReportFilters): Report[] => {
  return reports.filter(report => {
    // Filter by merchant
    if (filters.merchant && report.merchant !== filters.merchant) {
      return false;
    }
    
    // Filter by providers (multiple selection)
    if (filters.providers.length > 0 && !filters.providers.includes(report.provider)) {
      return false;
    }
    
    return true;
  });
};

/**
 * Paginates an array of items
 * @param items - Array to paginate
 * @param page - Current page (0-indexed)
 * @param itemsPerPage - Items per page
 * @returns Paginated slice of items
 */
export const paginateItems = <T>(items: T[], page: number, itemsPerPage: number): T[] => {
  const startIndex = page * itemsPerPage;
  return items.slice(startIndex, startIndex + itemsPerPage);
};

/**
 * Calculates total number of pages
 * @param totalItems - Total number of items
 * @param itemsPerPage - Items per page
 * @returns Total number of pages
 */
export const calculateTotalPages = (totalItems: number, itemsPerPage: number): number => {
  return Math.ceil(totalItems / itemsPerPage);
};
