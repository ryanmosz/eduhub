// API configuration utility
export const getApiUrl = () => {
  return import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '';
};

export const apiUrl = getApiUrl();

// Helper function to create full API URLs
export const apiEndpoint = (path: string) => {
  const base = getApiUrl();
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : '/' + path;
  return `${base}${normalizedPath}`;
};

// Fetch wrapper with default credentials
export const apiFetch = (path: string, options: RequestInit = {}) => {
  return fetch(apiEndpoint(path), {
    credentials: 'include',
    ...options,
  });
};
