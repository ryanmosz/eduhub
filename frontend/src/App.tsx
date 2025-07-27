import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth0 } from '@auth0/auth0-react';
import { AuthProvider } from '@/components/auth/AuthProvider';
import { MainLayout } from '@/components/layout/MainLayout';
import { Dashboard } from '@/pages/Dashboard';
import { ScheduleImport } from '@/pages/ScheduleImport';

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
  const { isAuthenticated, isLoading } = useAuth0();

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
        <Route path="embeds" element={<div>Media Embeds (Phase 5) - Coming Soon</div>} />
        <Route path="data" element={<div>Open Data (Phase 6) - Coming Soon</div>} />
        <Route path="workflows" element={<div>Workflows (Phase 7) - Coming Soon</div>} />
        <Route path="alerts" element={<div>Alerts (Phase 8) - Coming Soon</div>} />
      </Route>
      <Route path="/callback" element={<div>Processing login...</div>} />
    </Routes>
  );
}

function LoginPage() {
  const { loginWithRedirect } = useAuth0();

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
          <button
            onClick={() => loginWithRedirect()}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Sign in with Auth0
          </button>
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