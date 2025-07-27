import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from '@/hooks/useAuth';
import { MainLayout } from '@/components/layout/MainLayout';
import { Dashboard } from '@/pages/Dashboard';
import { StudentDashboard } from '@/pages/StudentDashboard';
import { ScheduleImport } from '@/pages/ScheduleImport';
import { EmbedPreview } from '@/pages/EmbedPreview';
import { OpenDataExplorer } from '@/pages/OpenDataExplorer';
import { WorkflowTemplates } from '@/pages/WorkflowTemplates';
import { RealTimeAlerts } from '@/pages/RealTimeAlerts';

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
  const { isAuthenticated, isLoading, user } = useAuth();

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

  // Check if user is a student
  const isStudent = user?.role === 'student';

  if (isStudent) {
    // Student routes - no MainLayout wrapper, just the dashboard
    return (
      <Routes>
        <Route path="/" element={<Navigate to="/student-dashboard" replace />} />
        <Route path="/student-dashboard" element={<StudentDashboard />} />
        <Route path="/callback" element={<CallbackHandler />} />
        <Route path="*" element={<Navigate to="/student-dashboard" replace />} />
      </Routes>
    );
  }

  // Admin/Developer routes with full MainLayout
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="schedule" element={<ScheduleImport />} />
        <Route path="embeds" element={<EmbedPreview />} />
        <Route path="data" element={<OpenDataExplorer />} />
        <Route path="workflows" element={<WorkflowTemplates />} />
        <Route path="alerts" element={<RealTimeAlerts />} />
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
  const [lastUser, setLastUser] = React.useState<string | null>(null);
  
  React.useEffect(() => {
    // Check for last logged in user from localStorage
    const savedUser = localStorage.getItem('lastAuthenticatedUser');
    if (savedUser) {
      setLastUser(savedUser);
    }
  }, []);
  
  const handleLogin = async (loginHint?: string) => {
    try {
      setIsRedirecting(true);
      setError(null);
      
      // Show loading state for a moment so user sees it
      setTimeout(() => {
        // Always require password, but can pre-fill email with login_hint
        const params = new URLSearchParams({
          return_to: window.location.origin + '/callback'
        });
        
        if (loginHint) {
          // Pre-fill the email but still require password
          params.append('login_hint', loginHint);
          // Force showing login screen even if session exists
          params.append('prompt', 'login');
        }
        
        window.location.href = `/auth/login?${params.toString()}`;
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
            <div className="space-y-4">
              {lastUser && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-700 font-medium mb-2">Continue as</p>
                  <p className="text-sm text-gray-700 mb-3">
                    {lastUser}
                  </p>
                  <button
                    onClick={() => handleLogin(lastUser)}
                    className="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Sign in as {lastUser}
                  </button>
                  <p className="text-xs text-gray-500 mt-2">
                    You'll need to enter your password
                  </p>
                </div>
              )}
              
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-gray-50 text-gray-500">Or</span>
                </div>
              </div>
              
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <p className="text-sm text-gray-700 font-medium mb-2">Different Account</p>
                <p className="text-xs text-gray-600 mb-3">
                  Force Auth0 to show the login screen with account selection
                </p>
                <button
                  onClick={() => {
                    setIsRedirecting(true);
                    setError(null);
                    // Force Auth0 to show login prompt
                    setTimeout(() => {
                      window.location.href = `/auth/login?prompt=login&return_to=${window.location.origin}/callback`;
                    }, 500);
                  }}
                  className="w-full flex justify-center py-2 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                >
                  Sign in as different user
                </button>
              </div>
              
              <div className="text-center">
                <p className="text-xs text-gray-500">
                  Test accounts: admin@example.com | dev@example.com | student@example.com
                </p>
              </div>
            </div>
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
