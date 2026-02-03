/**
 * Get the currency symbol for a given currency code
 */
export const getCurrencySymbol = (currencyCode: string): string => {
  const symbols: Record<string, string> = {
    USD: '$',
    EUR: '€',
    GBP: '£',
    CAD: 'C$',
    AUD: 'A$',
    JPY: '¥',
    CHF: 'CHF',
    CNY: '¥',
    INR: '₹',
    MXN: '$',
  };
  return symbols[currencyCode] || currencyCode;
};

/**
 * Format salary with currency symbol
 */
export const formatSalary = (salaryRange: string | null | undefined, currencyCode: string): string => {
  if (!salaryRange) return '';
  const symbol = getCurrencySymbol(currencyCode);
  return `${symbol}${salaryRange}`;
};
