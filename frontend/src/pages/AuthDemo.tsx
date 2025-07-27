import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { useAuth } from '@/hooks/useAuth';
import { Shield, User, Lock, CheckCircle2, AlertCircle, RefreshCw, Server, Users, Key } from 'lucide-react';

export function AuthDemo() {
  const { user, isAuthenticated } = useAuth();
  const [ploneSync, setPloneSync] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const checkPloneSync = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/auth/plone-sync-status', {
        credentials: 'include',
      });
      const data = await response.json();
      setPloneSync(data);
    } catch (error) {
      console.error('Failed to check Plone sync:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">OAuth2 + Plone Authentication</h1>
        <p className="mt-2 text-gray-600">
          Unified authentication combining Auth0 OAuth2 with Plone user management
        </p>
      </div>

      {/* Current User Status */}
      <Card className="p-6 bg-blue-50 border-blue-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Shield className="h-6 w-6 text-blue-600" />
          Current Authentication Status
        </h2>
        
        {isAuthenticated ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <span className="font-medium">Authenticated via Auth0</span>
            </div>
            
            <div className="bg-white p-4 rounded-lg border border-blue-200">
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-gray-600" />
                  <span className="font-medium">Email:</span> {user?.email}
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-gray-600" />
                  <span className="font-medium">Role:</span> 
                  <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs uppercase">
                    {user?.role || 'user'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Key className="h-4 w-4 text-gray-600" />
                  <span className="font-medium">Auth0 ID:</span> 
                  <span className="font-mono text-xs">{user?.sub}</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <span>Not authenticated</span>
          </div>
        )}
      </Card>

      {/* Plone Integration Status */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Server className="h-6 w-6" />
          Plone User Synchronization
        </h2>
        
        <button
          onClick={checkPloneSync}
          disabled={loading}
          className="mb-4 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400 flex items-center gap-2"
        >
          {loading ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" />
              Checking...
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4" />
              Check Plone Sync Status
            </>
          )}
        </button>

        {ploneSync && (
          <div className="space-y-4">
            {/* Sync Status */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-2">Synchronization Status:</h3>
              {ploneSync.synced ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-green-700">
                    <CheckCircle2 className="h-5 w-5" />
                    <span>User synchronized with Plone</span>
                  </div>
                  {ploneSync.plone_user && (
                    <div className="ml-7 space-y-1 text-sm text-gray-600">
                      <p>Plone Username: <span className="font-mono">{ploneSync.plone_user.username}</span></p>
                      <p>Plone Roles: {ploneSync.plone_user.roles?.join(', ') || 'Member'}</p>
                      {ploneSync.plone_user.groups?.length > 0 && (
                        <p>Groups: {ploneSync.plone_user.groups.join(', ')}</p>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-yellow-600">
                    <AlertCircle className="h-5 w-5" />
                    <span>User not yet synchronized with Plone</span>
                  </div>
                  <button
                    onClick={async () => {
                      setLoading(true);
                      try {
                        const response = await fetch('/api/auth/sync-with-plone', {
                          method: 'POST',
                          credentials: 'include',
                        });
                        const data = await response.json();
                        if (data.success) {
                          // Refresh sync status
                          await checkPloneSync();
                        }
                      } catch (error) {
                        console.error('Failed to sync with Plone:', error);
                      } finally {
                        setLoading(false);
                      }
                    }}
                    disabled={loading}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400 text-sm flex items-center gap-2"
                  >
                    <Users className="h-4 w-4" />
                    Sync Now
                  </button>
                </div>
              )}
            </div>

            {/* Integration Flow */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-3">Authentication Flow:</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-start gap-2">
                  <span className="font-mono bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">1</span>
                  <span>User logs in via Auth0 OAuth2</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="font-mono bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">2</span>
                  <span>JWT token validated with Auth0 JWKS</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="font-mono bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">3</span>
                  <span>System checks for existing Plone user by email</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="font-mono bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">4</span>
                  <span>Creates Plone user if needed (no password required)</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="font-mono bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">5</span>
                  <span>Combines Auth0 claims with Plone roles/groups</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Lock className="h-5 w-5" />
            Security Features
          </h3>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              <span>RS256 JWT signature validation</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              <span>Token expiration and age checks</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              <span>JWKS key rotation support</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              <span>Graceful fallback if Plone is down</span>
            </li>
          </ul>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Users className="h-5 w-5" />
            User Management
          </h3>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              <span>Automatic Plone user creation</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              <span>Email-based user matching</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              <span>Role mapping from Auth0 metadata</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              <span>Combined permissions model</span>
            </li>
          </ul>
        </Card>
      </div>

      {/* Code Locations */}
      <Card className="p-6 bg-gray-50">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Implementation Details</h3>
        <div className="space-y-2 text-sm">
          <div className="bg-white p-3 rounded border border-gray-200">
            <code className="text-blue-600">src/eduhub/auth/dependencies.py</code>
            <p className="text-gray-600 text-xs mt-1">JWT validation and user dependency injection</p>
          </div>
          <div className="bg-white p-3 rounded border border-gray-200">
            <code className="text-blue-600">src/eduhub/auth/plone_bridge.py</code>
            <p className="text-gray-600 text-xs mt-1">Auth0 to Plone user synchronization logic</p>
          </div>
          <div className="bg-white p-3 rounded border border-gray-200">
            <code className="text-blue-600">src/eduhub/auth/models.py</code>
            <p className="text-gray-600 text-xs mt-1">Unified User model with Auth0 + Plone data</p>
          </div>
        </div>
      </Card>

      {/* Benefits */}
      <Card className="p-6 bg-green-50 border-green-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Benefits of This Approach</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <span>Users don't need separate Plone passwords</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <span>Single sign-on across all systems</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <span>Preserves existing Plone permissions</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <span>Works even when Plone is offline</span>
          </div>
        </div>
      </Card>
    </div>
  );
}