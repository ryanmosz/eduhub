import { Card } from '@/components/ui/Card';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useAnnouncements } from '@/hooks/useCourses';
import {
  Calendar,
  FileVideo,
  Database,
  Workflow,
  Bell,
  CheckCircle2,
  Clock,
  AlertCircle,
  Shield,
  RefreshCw
} from 'lucide-react';

const stats = [
  { name: 'Total Schedules', value: '12', icon: Calendar, status: 'active' },
  { name: 'Media Embeds', value: '47', icon: FileVideo, status: 'active' },
  { name: 'Public Data Sets', value: '8', icon: Database, status: 'recovered' },
  { name: 'Active Workflows', value: '15', icon: Workflow, status: 'recovered' },
  { name: 'Recent Alerts', value: '23', icon: Bell, status: 'active' },
];

const recentActivity = [
  { id: 1, type: 'schedule', message: 'New schedule imported for Spring 2024', time: '2 hours ago', icon: Calendar },
  { id: 2, type: 'embed', message: 'Added YouTube video to Physics 101', time: '4 hours ago', icon: FileVideo },
  { id: 3, type: 'workflow', message: 'Course approval workflow completed', time: '1 day ago', icon: Workflow },
  { id: 4, type: 'alert', message: 'System maintenance scheduled', time: '2 days ago', icon: Bell },
];

export function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: announcements, isLoading: announcementsLoading, refetch: refetchAnnouncements } = useAnnouncements(10);
  
  return (
    <div className="space-y-6">
      {/* Admin Header Banner */}
      <div className="bg-gradient-to-r from-slate-700 to-slate-800 text-white p-6 rounded-lg shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Shield className="h-8 w-8" />
              <span>ADMINISTRATOR PORTAL</span>
            </h1>
            <p className="mt-2 text-slate-200">
              Logged in as: <span className="font-semibold">{user?.email}</span>
            </p>
          </div>
          <div className="text-right">
            <span className="bg-white/20 px-3 py-1 rounded-md text-sm uppercase tracking-wider">
              Role: {user?.role || 'ADMIN'}
            </span>
            <p className="text-xs text-slate-300 mt-2">Full system access</p>
          </div>
        </div>
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard Overview</h2>
        <p className="mt-1 text-sm text-gray-600">
          Manage your educational content and workflows from one central location.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.name} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="mt-2 text-3xl font-semibold text-gray-900">{stat.value}</p>
                </div>
                <div className={cn(
                  "p-3 rounded-full",
                  stat.status === 'active' ? "bg-blue-50" : "bg-yellow-50"
                )}>
                  <Icon className={cn(
                    "h-6 w-6",
                    stat.status === 'active' ? "text-blue-600" : "text-yellow-600"
                  )} />
                </div>
              </div>
              {stat.status === 'recovered' && (
                <p className="mt-2 text-xs text-yellow-600 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  Recently recovered
                </p>
              )}
            </div>
          );
        })}
      </div>

      {/* Recent activity with Plone Announcements */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Recent Activity & Announcements</h2>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">
              {announcementsLoading ? 'Loading from Plone...' : 'Synced with Plone'}
            </span>
            {!announcementsLoading && (
              <button 
                onClick={() => refetchAnnouncements()}
                className="text-sm text-blue-600 hover:text-blue-700 p-1"
                title="Refresh announcements"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
        <div className="divide-y divide-gray-200">
          {/* Show Plone announcements first */}
          {announcements && announcements.slice(0, 3).map((announcement) => {
            const Icon = announcement.type === 'success' ? CheckCircle2 : 
                         announcement.type === 'warning' ? AlertCircle : Bell;
            return (
              <div key={`announce-${announcement.id}`} className="px-6 py-4 flex items-center gap-4">
                <div className="p-2 bg-blue-50 rounded-full">
                  <Icon className="h-5 w-5 text-blue-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">{announcement.title}</p>
                  <p className="text-xs text-gray-600 mt-1">{announcement.content}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(announcement.created).toLocaleDateString()} 
                    {announcement.author && ` • By ${announcement.author}`}
                  </p>
                </div>
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">Plone</span>
              </div>
            );
          })}
          
          {/* Then show recent system activity */}
          {recentActivity.slice(0, announcements ? 2 : 4).map((activity) => {
            const Icon = activity.icon;
            return (
              <div key={activity.id} className="px-6 py-4 flex items-center gap-4">
                <div className="p-2 bg-gray-50 rounded-full">
                  <Icon className="h-5 w-5 text-gray-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">{activity.message}</p>
                  <p className="text-xs text-gray-500">{activity.time}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* System status */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">API Services</span>
            <span className="flex items-center gap-2 text-sm text-green-600">
              <CheckCircle2 className="h-4 w-4" />
              All systems operational
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Phase 6 & 7 Features</span>
            <span className="flex items-center gap-2 text-sm text-yellow-600">
              <Clock className="h-4 w-4" />
              Testing in progress
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">WebSocket Alerts</span>
            <span className="flex items-center gap-2 text-sm text-blue-600">
              <AlertCircle className="h-4 w-4" />
              Backend in development
            </span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => navigate('/schedule')}
            className="p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all group"
          >
            <Calendar className="h-8 w-8 text-gray-400 group-hover:text-blue-600 mx-auto mb-3" />
            <p className="font-medium text-gray-700 group-hover:text-blue-700">Import Schedule</p>
            <p className="text-xs text-gray-500 mt-1">Upload CSV schedules</p>
          </button>
          
          <button
            onClick={() => navigate('/embeds')}
            className="p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-all group"
          >
            <FileVideo className="h-8 w-8 text-gray-400 group-hover:text-purple-600 mx-auto mb-3" />
            <p className="font-medium text-gray-700 group-hover:text-purple-700">Embed Media</p>
            <p className="text-xs text-gray-500 mt-1">Add rich media content</p>
          </button>
          
          <button
            onClick={() => navigate('/data')}
            className="p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-400 hover:bg-green-50 transition-all group"
          >
            <Database className="h-8 w-8 text-gray-400 group-hover:text-green-600 mx-auto mb-3" />
            <p className="font-medium text-gray-700 group-hover:text-green-700">Browse Data</p>
            <p className="text-xs text-gray-500 mt-1">Explore public content</p>
          </button>
          
          <button
            onClick={() => navigate('/workflows')}
            className="p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-orange-400 hover:bg-orange-50 transition-all group"
          >
            <Workflow className="h-8 w-8 text-gray-400 group-hover:text-orange-600 mx-auto mb-3" />
            <p className="font-medium text-gray-700 group-hover:text-orange-700">Manage Workflows</p>
            <p className="text-xs text-gray-500 mt-1">Configure approvals</p>
          </button>
        </div>
      </div>
    </div>
  );
}

function cn(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}
