// API configuration utility
export const getApiUrl = () => {
  const url = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  console.log('API URL:', url, 'VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
  return url;
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
