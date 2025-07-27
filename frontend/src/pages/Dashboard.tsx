import { Card } from '@/components/ui/card';
import {
  Calendar,
  FileVideo,
  Database,
  Workflow,
  Bell,
  CheckCircle2,
  Clock,
  AlertCircle
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
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Welcome to EduHub Admin</h1>
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

      {/* Recent activity */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {recentActivity.map((activity) => {
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
    </div>
  );
}

function cn(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}
