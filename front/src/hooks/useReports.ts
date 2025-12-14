import { useState, useMemo } from 'react';
import type { Report, ReportFilters } from '@/types/report';
import { filterReports, paginateItems, calculateTotalPages } from '@/utils/reportHelpers';
import { PAGINATION } from '@/constants/reports';

interface UseReportsReturn {
  filteredReports: Report[];
  paginatedReports: Report[];
  currentPage: number;
  totalPages: number;
  filters: ReportFilters;
  handleFilterChange: (key: string, value: string | string[]) => void;
  handleClearFilters: () => void;
  handlePageChange: (page: number) => void;
}

/**
 * Custom hook for managing reports state and logic
 * @param reports - Array of all reports
 * @returns Object with filtered/paginated reports and handler functions
 */
export const useReports = (reports: Report[]): UseReportsReturn => {
  const [filters, setFilters] = useState<ReportFilters>({
    merchant: '',
    providers: []
  });
  const [currentPage, setCurrentPage] = useState(0);

  // Filter reports based on active filters
  const filteredReports = useMemo(
    () => filterReports(reports, filters),
    [reports, filters]
  );

  // Paginate filtered reports
  const paginatedReports = useMemo(
    () => paginateItems(filteredReports, currentPage, PAGINATION.ITEMS_PER_PAGE),
    [filteredReports, currentPage]
  );

  // Calculate total pages
  const totalPages = useMemo(
    () => calculateTotalPages(filteredReports.length, PAGINATION.ITEMS_PER_PAGE),
    [filteredReports.length]
  );

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
  };

  return {
    filteredReports,
    paginatedReports,
    currentPage,
    totalPages,
    filters,
    handleFilterChange,
    handleClearFilters,
    handlePageChange,
  };
};
