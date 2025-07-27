import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from '@/hooks/useAuth';
import { MainLayout } from '@/components/layout/MainLayout';
import { Dashboard } from '@/pages/Dashboard';
import { ScheduleImport } from '@/pages/ScheduleImport';
import { EmbedPreview } from '@/pages/EmbedPreview';
import { OpenDataExplorer } from '@/pages/OpenDataExplorer';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

function AuthenticatedApp() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="schedule" element={<ScheduleImport />} />
        <Route path="embeds" element={<EmbedPreview />} />
        <Route path="data" element={<OpenDataExplorer />} />
        <Route path="workflows" element={<div>Workflows (Phase 7) - Coming Soon</div>} />
        <Route path="alerts" element={<div>Alerts (Phase 8) - Coming Soon</div>} />
      </Route>
      <Route path="/callback" element={<CallbackHandler />} />
    </Routes>
  );
}

function CallbackHandler() {
  const { checkAuth } = useAuth();
  
  React.useEffect(() => {
    // After backend sets the cookie and redirects here, check auth status
    checkAuth().then(() => {
      // Redirect to home after auth check
      window.location.href = '/';
    });
  }, []);
  
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Processing login...</p>
      </div>
    </div>
  );
}

function LoginPage() {
  const [isRedirecting, setIsRedirecting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  
  const handleLogin = async () => {
    try {
      setIsRedirecting(true);
      setError(null);
      
      // Show loading state for a moment so user sees it
      setTimeout(() => {
        // Redirect to backend auth endpoint with return URL
        window.location.href = `/auth/login?return_to=${encodeURIComponent(window.location.origin + '/callback')}`;
      }, 500);
    } catch (err) {
      console.error('Login error:', err);
      setError('Failed to redirect to login. Please check console.');
      setIsRedirecting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Welcome to EduHub Admin
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to manage your educational content
          </p>
        </div>
        <div className="mt-8 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
              <strong className="font-bold">Error: </strong>
              <span className="block sm:inline">{error}</span>
            </div>
          )}
          {isRedirecting ? (
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-lg font-semibold text-gray-700">Redirecting to Auth0...</p>
              <p className="mt-2 text-sm text-gray-500">Please wait while we secure your login</p>
            </div>
          ) : (
            <button
              onClick={handleLogin}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Sign in with Auth0
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <AuthenticatedApp />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
