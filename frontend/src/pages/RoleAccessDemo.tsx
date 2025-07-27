import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { useAuth } from '@/hooks/useAuth';
import { Shield, Users, Lock, CheckCircle2, AlertCircle, Key, UserCheck, Settings } from 'lucide-react';

export function RoleAccessDemo() {
  const { user } = useAuth();
  const [accessTest, setAccessTest] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testAccess = async (endpoint: string) => {
    setLoading(true);
    try {
      const response = await fetch(endpoint, {
        credentials: 'include',
      });
      const data = await response.json();
      setAccessTest({
        endpoint,
        status: response.status,
        allowed: response.ok,
        data
      });
    } catch (error) {
      setAccessTest({
        endpoint,
        status: 0,
        allowed: false,
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  // Determine user's role from email
  const userRole = user?.email?.includes('admin') ? 'Manager' : 
                   user?.email?.includes('student') ? 'Student' : 
                   user?.email?.includes('dev') ? 'Developer' : 'Member';

  const ploneRoles = userRole === 'Manager' ? ['Member', 'Authenticated', 'Manager'] :
                     userRole === 'Student' ? ['Member', 'Authenticated', 'Student'] :
                     userRole === 'Developer' ? ['Member', 'Authenticated', 'Editor'] :
                     ['Member', 'Authenticated'];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Role-Based Access Control</h1>
        <p className="mt-2 text-gray-600">
          Plone roles integrated with our permission system
        </p>
      </div>

      {/* Current User Role Status */}
      <Card className="p-6 bg-blue-50 border-blue-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <UserCheck className="h-6 w-6 text-blue-600" />
          Your Access Level
        </h2>
        
        <div className="space-y-3">
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-gray-600" />
                <span className="font-medium">Email:</span> {user?.email}
              </div>
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-gray-600" />
                <span className="font-medium">System Role:</span> 
                <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs uppercase">
                  {userRole}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Key className="h-4 w-4 text-gray-600" />
                <span className="font-medium">Plone Roles:</span> 
                <div className="flex gap-1">
                  {ploneRoles.map(role => (
                    <span key={role} className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs">
                      {role}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Role Hierarchy */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Settings className="h-6 w-6" />
          Role Hierarchy & Permissions
        </h2>
        
        <div className="space-y-4">
          {/* Manager Role */}
          <div className={`p-4 rounded-lg border-2 ${userRole === 'Manager' ? 'border-green-400 bg-green-50' : 'border-gray-200'}`}>
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Shield className="h-5 w-5 text-red-600" />
              Manager (Admin)
            </h3>
            <p className="text-sm text-gray-600 mt-1">Full system access</p>
            <div className="mt-2 space-y-1 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>Create, edit, delete all content</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>Manage users and permissions</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>Import schedules</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>Send system alerts</span>
              </div>
            </div>
          </div>

          {/* Editor/Developer Role */}
          <div className={`p-4 rounded-lg border-2 ${userRole === 'Developer' ? 'border-green-400 bg-green-50' : 'border-gray-200'}`}>
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Shield className="h-5 w-5 text-orange-600" />
              Editor (Developer)
            </h3>
            <p className="text-sm text-gray-600 mt-1">Content management access</p>
            <div className="mt-2 space-y-1 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>Create and edit content</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>Import schedules</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-yellow-600" />
                <span>Cannot delete content</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-yellow-600" />
                <span>Cannot manage users</span>
              </div>
            </div>
          </div>

          {/* Student Role */}
          <div className={`p-4 rounded-lg border-2 ${userRole === 'Student' ? 'border-green-400 bg-green-50' : 'border-gray-200'}`}>
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Shield className="h-5 w-5 text-blue-600" />
              Student
            </h3>
            <p className="text-sm text-gray-600 mt-1">Read-only access</p>
            <div className="mt-2 space-y-1 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>View courses and schedules</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>Export personal data</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <span>Cannot edit content</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <span>Cannot access admin features</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Access Testing */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Lock className="h-6 w-6" />
          Test Your Access
        </h2>
        
        <div className="space-y-3">
          <button
            onClick={() => testAccess('/api/rbac/public-read')}
            disabled={loading}
            className="w-full text-left p-3 border rounded-lg hover:bg-gray-50 disabled:bg-gray-100"
          >
            <div className="flex justify-between items-center">
              <span className="font-medium">View Courses (All roles)</span>
              <span className="text-sm text-gray-500">GET /api/rbac/public-read</span>
            </div>
          </button>

          <button
            onClick={() => testAccess('/api/rbac/editor-access')}
            disabled={loading}
            className="w-full text-left p-3 border rounded-lg hover:bg-gray-50 disabled:bg-gray-100"
          >
            <div className="flex justify-between items-center">
              <span className="font-medium">Import Schedule (Editor+)</span>
              <span className="text-sm text-gray-500">GET /api/rbac/editor-access</span>
            </div>
          </button>

          <button
            onClick={() => testAccess('/api/rbac/manager-only')}
            disabled={loading}
            className="w-full text-left p-3 border rounded-lg hover:bg-gray-50 disabled:bg-gray-100"
          >
            <div className="flex justify-between items-center">
              <span className="font-medium">Manage Users (Manager only)</span>
              <span className="text-sm text-gray-500">GET /api/rbac/manager-only</span>
            </div>
          </button>
        </div>

        {accessTest && (
          <div className="mt-4 p-4 rounded-lg bg-gray-50">
            <h3 className="font-semibold mb-2">Test Result:</h3>
            <div className="space-y-1 text-sm">
              <p>Endpoint: <code className="bg-gray-200 px-1 rounded">{accessTest.endpoint}</code></p>
              <p>Status: <span className={accessTest.allowed ? 'text-green-600' : 'text-red-600'}>
                {accessTest.status} {accessTest.allowed ? '✅ Allowed' : '❌ Denied'}
              </span></p>
              {accessTest.error && <p className="text-red-600">Error: {accessTest.error}</p>}
            </div>
          </div>
        )}
      </Card>

      {/* Integration with Plone */}
      <Card className="p-6 bg-gray-50">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Plone Integration</h3>
        <div className="space-y-2 text-sm">
          <div className="flex items-start gap-2">
            <span className="font-mono bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">1</span>
            <span>User logs in via Auth0 OAuth2</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-mono bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">2</span>
            <span>System maps Auth0 email to Plone user</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-mono bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">3</span>
            <span>Plone roles (Manager, Editor, Member) are retrieved</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-mono bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">4</span>
            <span>FastAPI enforces permissions based on combined roles</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-mono bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">5</span>
            <span>Content operations respect Plone's permission model</span>
          </div>
        </div>
      </Card>

      {/* Benefits */}
      <Card className="p-6 bg-green-50 border-green-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Why This Matters</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <span>Existing Plone permissions preserved</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <span>No duplicate role management</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <span>Granular access control</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <span>API-level enforcement</span>
          </div>
        </div>
      </Card>
    </div>
  );
}