import { DATE_FORMAT_OPTIONS } from '@/constants/reports';

/**
 * Formats a date string to a localized format
 * @param dateString - ISO date string
 * @param locale - Locale to use (default: 'en-US')
 * @returns Formatted date string
 */
export const formatDate = (dateString: string, locale: string = 'en-US'): string => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat(locale, DATE_FORMAT_OPTIONS).format(date);
};

/**
 * Formats a number with locale-specific thousands separators
 * @param value - Number to format
 * @param locale - Locale to use (default: 'en-US')
 * @returns Formatted number string
 */
export const formatNumber = (value: number, locale: string = 'en-US'): string => {
  return value.toLocaleString(locale);
};

/**
 * Scrolls to the top of the page with smooth behavior
 */
export const scrollToTop = (): void => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
};
