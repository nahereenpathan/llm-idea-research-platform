/**
 * Safely extracts and formats user-facing error messages from API and network errors.
 * Guarantees a string output suitable for direct React JSX rendering.
 */
export function formatAuthError(err, fallback = 'An unexpected error occurred. Please try again.') {
  if (!err) return fallback;

  // Handle direct string errors
  if (typeof err === 'string') return err;

  // Handle network disconnection or server unreachable
  if (
    err.code === 'ERR_NETWORK' ||
    (!err.response && (err.message?.toLowerCase().includes('network') || err.message?.toLowerCase().includes('failed to fetch')))
  ) {
    return 'Unable to connect to authentication server. Please ensure the backend is running.';
  }

  // Gateway and proxy errors (e.g. Vite proxy ECONNREFUSED)
  if (err.response?.status === 502 || err.response?.status === 503 || err.response?.status === 504) {
    return 'Authentication service is temporarily unavailable. Please try again shortly.';
  }

  // Check if proxy returned 500 without a structured detail
  if (err.response?.status === 500 && !err.response?.data?.detail) {
    return 'Authentication server error. Please verify the backend is running and healthy.';
  }

  const detail = err.response?.data?.detail;

  // If detail is a plain string
  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail.trim();
  }

  // If detail is a list of Pydantic validation errors
  if (Array.isArray(detail) && detail.length > 0) {
    const formatted = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          let msg = item.msg || '';
          if (msg.startsWith('Value error, ')) {
            msg = msg.replace(/^Value error,\s*/i, '');
          }
          const loc = Array.isArray(item.loc) ? item.loc : [];
          const field = loc.length > 0 ? loc[loc.length - 1] : '';
          if (field && field !== 'body') {
            const fieldLabel =
              field === 'full_name'
                ? 'Full name'
                : field.charAt(0).toUpperCase() + field.slice(1);
            return `${fieldLabel}: ${msg}`;
          }
          return msg;
        }
        return null;
      })
      .filter(Boolean);

    if (formatted.length > 0) {
      return formatted.join('. ');
    }
  }

  // If detail is a dictionary
  if (detail && typeof detail === 'object') {
    const msg = detail.msg || detail.message;
    if (typeof msg === 'string') return msg;
  }

  // Check err.response.data.message
  if (typeof err.response?.data?.message === 'string') {
    return err.response.data.message;
  }

  return fallback;
}
