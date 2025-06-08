/**
 * Utility functions for formatting data
 */

/**
 * Format a date string to a localized date format
 * @param dateString ISO date string
 * @returns Formatted date string
 */
export const formatDate = (dateString: string): string => {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('pt-BR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  } catch (error) {
    console.error('Error formatting date:', error);
    return dateString;
  }
};

/**
 * Format a number as currency
 * @param value Number to format
 * @param currency Currency code (default: 'BRL')
 * @returns Formatted currency string
 */
export const formatCurrency = (value: number, currency = 'BRL'): string => {
  if (value === null || value === undefined) return '';
  
  try {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency,
    }).format(value);
  } catch (error) {
    console.error('Error formatting currency:', error);
    return value.toString();
  }
};

/**
 * Truncate a string to a maximum length and add ellipsis if needed
 * @param text Text to truncate
 * @param maxLength Maximum length
 * @returns Truncated text
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  
  return `${text.substring(0, maxLength)}...`;
};

/**
 * Format a status string to be more readable
 * @param status Status string
 * @returns Formatted status string
 */
export const formatStatus = (status: string): string => {
  if (!status) return '';
  
  // Replace underscores with spaces and capitalize each word
  return status
    .replace(/_/g, ' ')
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};
