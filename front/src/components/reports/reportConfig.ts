import { UI_MESSAGES } from '@/constants/reports';

type SeverityKey = 'low' | 'medium' | 'high' | 'critical';
type StatusKey = 'pending' | 'in-progress' | 'resolved' | 'rejected';

/**
 * Configuration for severity badge styling
 */
export const SEVERITY_CONFIG: Record<SeverityKey, { className: string; label: string }> = {
  low: {
    className: 'bg-blue-100 text-blue-800',
    label: UI_MESSAGES.SEVERITY.LOW,
  },
  medium: {
    className: 'bg-yellow-100 text-yellow-800',
    label: UI_MESSAGES.SEVERITY.MEDIUM,
  },
  high: {
    className: 'bg-orange-100 text-orange-800',
    label: UI_MESSAGES.SEVERITY.HIGH,
  },
  critical: {
    className: 'bg-red-100 text-red-800',
    label: UI_MESSAGES.SEVERITY.CRITICAL,
  },
};

/**
 * Configuration for status text and labels
 */
export const STATUS_CONFIG: Record<StatusKey, string> = {
  pending: UI_MESSAGES.STATUS.PENDING,
  'in-progress': UI_MESSAGES.STATUS.IN_PROGRESS,
  resolved: UI_MESSAGES.STATUS.RESOLVED,
  rejected: UI_MESSAGES.STATUS.REJECTED,
};

/**
 * Gets the severity configuration for a given severity level
 */
export const getSeverityConfig = (severity: string) => {
  return SEVERITY_CONFIG[severity as SeverityKey] || SEVERITY_CONFIG.low;
};

/**
 * Gets the status text for a given status
 */
export const getStatusText = (status: string): string => {
  return STATUS_CONFIG[status as StatusKey] || STATUS_CONFIG.pending;
};
