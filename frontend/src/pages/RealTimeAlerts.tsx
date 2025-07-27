import React, { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Bell, BellOff, CheckCircle2, AlertCircle, Info, MessageSquare, Clock, Settings, Send, Trash2 } from 'lucide-react';

interface Alert {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  channel: 'web' | 'slack' | 'email';
}

interface AlertPreference {
  type: string;
  web: boolean;
  slack: boolean;
  email: boolean;
}

export function RealTimeAlerts() {
  const [activeTab, setActiveTab] = useState<'feed' | 'compose' | 'settings'>('feed');
  const [alerts, setAlerts] = useState<Alert[]>([
    {
      id: '1',
      type: 'success',
      title: 'Schedule Import Complete',
      message: 'Successfully imported 45 events for Spring 2025',
      timestamp: '2 minutes ago',
      read: false,
      channel: 'web'
    },
    {
      id: '2',
      type: 'info',
      title: 'New Workflow Assignment',
      message: 'You have been assigned to review "Physics 101 Course Update"',
      timestamp: '15 minutes ago',
      read: false,
      channel: 'web'
    },
    {
      id: '3',
      type: 'warning',
      title: 'System Maintenance Scheduled',
      message: 'The system will be under maintenance on Friday 2-4 AM EST',
      timestamp: '1 hour ago',
      read: true,
      channel: 'slack'
    },
    {
      id: '4',
      type: 'error',
      title: 'Import Failed',
      message: 'Failed to import schedule: Invalid date format in row 23',
      timestamp: '3 hours ago',
      read: true,
      channel: 'web'
    }
  ]);

  const [preferences, setPreferences] = useState<AlertPreference[]>([
    { type: 'Schedule Updates', web: true, slack: true, email: false },
    { type: 'Workflow Notifications', web: true, slack: false, email: true },
    { type: 'System Alerts', web: true, slack: true, email: true },
    { type: 'Content Changes', web: false, slack: false, email: true }
  ]);

  const [composeAlert, setComposeAlert] = useState({
    title: '',
    message: '',
    priority: 'medium',
    category: 'system',
    audience: 'all'
  });

  const wsRef = useRef<WebSocket | null>(null);
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  // Connect to real WebSocket endpoint
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        setWsStatus('connecting');
        const websocket = new WebSocket('ws://localhost:8000/alerts/ws');
        
        websocket.onopen = () => {
          console.log('Admin WebSocket connected');
          setWsStatus('connected');
        };
        
        websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('Admin received message:', data);
            
            // Handle different message types
            if (data.type === 'connected' || data.type === 'pong') {
              // Connection or heartbeat messages
              return;
            }
            
            // Add new alert to the list
            // Map priority levels to alert types for display
            const typeMap: { [key: string]: Alert['type'] } = {
              'low': 'info',
              'medium': 'info',
              'high': 'warning',
              'critical': 'error'
            };
            
            const newAlert: Alert = {
              id: data.id || Date.now().toString(),
              type: typeMap[data.priority] || data.type || 'info',
              title: data.title,
              message: data.message,
              timestamp: 'just now',
              read: false,
              channel: 'web'
            };
            setAlerts(prev => [newAlert, ...prev]);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };
        
        websocket.onclose = () => {
          console.log('Admin WebSocket disconnected');
          setWsStatus('disconnected');
          // Reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };
        
        websocket.onerror = (error) => {
          console.error('Admin WebSocket error:', error);
          setWsStatus('disconnected');
        };
        
        wsRef.current = websocket;
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setWsStatus('disconnected');
        // Retry after 3 seconds
        setTimeout(connectWebSocket, 3000);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const markAsRead = (alertId: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, read: true } : alert
    ));
  };

  const markAllAsRead = () => {
    setAlerts(prev => prev.map(alert => ({ ...alert, read: true })));
  };

  const deleteAlert = (alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'success': return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'warning': return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'error': return <AlertCircle className="h-5 w-5 text-red-500" />;
      default: return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const renderAlertFeed = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold text-gray-900">Alert Feed</h2>
          <span className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full ${
            wsStatus === 'connected' ? 'bg-green-100 text-green-700' :
            wsStatus === 'connecting' ? 'bg-yellow-100 text-yellow-700' :
            'bg-red-100 text-red-700'
          }`}>
            <span className={`w-2 h-2 rounded-full ${
              wsStatus === 'connected' ? 'bg-green-500' :
              wsStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
              'bg-red-500'
            }`}></span>
            {wsStatus === 'connected' ? 'Live' : wsStatus === 'connecting' ? 'Connecting...' : 'Offline'}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={markAllAsRead}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Mark all as read
          </button>
          <select className="px-3 py-1 text-sm border border-gray-300 rounded-md">
            <option>All Alerts</option>
            <option>Unread Only</option>
            <option>Web</option>
            <option>Slack</option>
            <option>Email</option>
          </select>
        </div>
      </div>

      <div className="space-y-3">
        {alerts.length === 0 ? (
          <Card className="p-8 text-center">
            <Bell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No alerts yet</p>
          </Card>
        ) : (
          alerts.map((alert) => (
            <Card 
              key={alert.id} 
              className={`p-4 transition-all ${!alert.read ? 'bg-blue-50/50 border-blue-300 shadow-sm' : ''}`}
            >
              <div className="flex items-start gap-4">
                <div className="mt-1">{getAlertIcon(alert.type)}</div>
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className={`font-medium ${!alert.read ? 'text-gray-900' : 'text-gray-700'}`}>
                        {alert.title}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>{alert.timestamp}</span>
                        <span className="flex items-center gap-1">
                          {alert.channel === 'slack' && <MessageSquare className="h-3 w-3" />}
                          {alert.channel === 'email' && <Bell className="h-3 w-3" />}
                          {alert.channel}
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {!alert.read && (
                        <button
                          onClick={() => markAsRead(alert.id)}
                          className="text-blue-600 hover:text-blue-700"
                          title="Mark as read"
                        >
                          <CheckCircle2 className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteAlert(alert.id)}
                        className="text-gray-400 hover:text-red-600"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 bg-blue-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-700">Unread</p>
              <p className="text-2xl font-bold text-blue-900">
                {alerts.filter(a => !a.read).length}
              </p>
            </div>
            <Bell className="h-8 w-8 text-blue-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Today</p>
              <p className="text-2xl font-bold text-gray-900">12</p>
            </div>
            <Clock className="h-8 w-8 text-gray-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">This Week</p>
              <p className="text-2xl font-bold text-gray-900">47</p>
            </div>
            <Bell className="h-8 w-8 text-gray-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Channels</p>
              <p className="text-2xl font-bold text-gray-900">3</p>
            </div>
            <Settings className="h-8 w-8 text-gray-500" />
          </div>
        </Card>
      </div>
    </div>
  );

  const renderCompose = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Compose Alert</h2>
      
      <Card className="p-6">
        <form className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                value={composeAlert.priority}
                onChange={(e) => setComposeAlert({...composeAlert, priority: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                value={composeAlert.category}
                onChange={(e) => setComposeAlert({...composeAlert, category: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="system">System</option>
                <option value="workflow">Workflow</option>
                <option value="schedule">Schedule</option>
                <option value="content">Content</option>
                <option value="security">Security</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title
            </label>
            <input
              type="text"
              value={composeAlert.title}
              onChange={(e) => setComposeAlert({...composeAlert, title: e.target.value})}
              placeholder="Alert title..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Message
            </label>
            <textarea
              value={composeAlert.message}
              onChange={(e) => setComposeAlert({...composeAlert, message: e.target.value})}
              placeholder="Alert message..."
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Audience
            </label>
            <select
              value={composeAlert.audience}
              onChange={(e) => setComposeAlert({...composeAlert, audience: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="all">All Users</option>
              <option value="admins">Administrators Only</option>
              <option value="instructors">Instructors Only</option>
              <option value="students">Students Only</option>
            </select>
          </div>

          <div className="border-t pt-4 flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Alert will be sent via: Web, Slack, Email
            </div>
            <button
              type="button"
              onClick={async () => {
                try {
                  const response = await fetch('/alerts/send', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                      title: composeAlert.title,
                      message: composeAlert.message,
                      priority: composeAlert.priority,
                      category: composeAlert.category,
                      channels: ['websocket'], // WebSocket channel for real-time
                    }),
                  });
                  
                  if (response.ok) {
                    alert('Alert sent successfully!');
                    setComposeAlert({ title: '', message: '', priority: 'medium', category: 'system', audience: 'all' });
                  } else {
                    const error = await response.json();
                    alert(`Failed to send alert: ${error.detail || 'Unknown error'}`);
                  }
                } catch (error) {
                  alert(`Failed to send alert: ${error}`);
                }
              }}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <Send className="h-4 w-4" />
              Send Alert
            </button>
          </div>
        </form>
      </Card>

      <Card className="p-6 bg-yellow-50 border-yellow-200">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
          <div>
            <h3 className="font-medium text-yellow-900">Alert Guidelines</h3>
            <ul className="mt-2 text-sm text-yellow-800 space-y-1">
              <li>• Keep messages concise and actionable</li>
              <li>• Use appropriate alert types (info, success, warning, error)</li>
              <li>• Consider user timezone when scheduling alerts</li>
              <li>• Avoid sending non-critical alerts outside business hours</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Alert Preferences</h2>

      <Card className="p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Delivery Channels</h3>
        <div className="space-y-4">
          <table className="min-w-full">
            <thead>
              <tr className="text-sm text-gray-500">
                <th className="text-left py-2">Alert Type</th>
                <th className="text-center py-2">Web</th>
                <th className="text-center py-2">Slack</th>
                <th className="text-center py-2">Email</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {preferences.map((pref, index) => (
                <tr key={pref.type}>
                  <td className="py-3 text-sm font-medium text-gray-900">{pref.type}</td>
                  <td className="py-3 text-center">
                    <input
                      type="checkbox"
                      checked={pref.web}
                      onChange={(e) => {
                        const newPrefs = [...preferences];
                        newPrefs[index].web = e.target.checked;
                        setPreferences(newPrefs);
                      }}
                      className="h-4 w-4 text-blue-600 rounded"
                    />
                  </td>
                  <td className="py-3 text-center">
                    <input
                      type="checkbox"
                      checked={pref.slack}
                      onChange={(e) => {
                        const newPrefs = [...preferences];
                        newPrefs[index].slack = e.target.checked;
                        setPreferences(newPrefs);
                      }}
                      className="h-4 w-4 text-blue-600 rounded"
                    />
                  </td>
                  <td className="py-3 text-center">
                    <input
                      type="checkbox"
                      checked={pref.email}
                      onChange={(e) => {
                        const newPrefs = [...preferences];
                        newPrefs[index].email = e.target.checked;
                        setPreferences(newPrefs);
                      }}
                      className="h-4 w-4 text-blue-600 rounded"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quiet Hours</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Enable Quiet Hours</p>
              <p className="text-sm text-gray-600">Mute non-critical alerts during specified hours</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">From</label>
              <input type="time" value="22:00" className="w-full px-3 py-2 border border-gray-300 rounded-md" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">To</label>
              <input type="time" value="08:00" className="w-full px-3 py-2 border border-gray-300 rounded-md" />
            </div>
          </div>
        </div>
      </Card>

      <div className="flex justify-end">
        <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
          Save Preferences
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Real-time Alerts</h1>
        <p className="mt-2 text-gray-600">
          Stay informed with instant notifications across multiple channels.
        </p>
      </div>

      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('feed')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'feed'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Alert Feed
          </button>
          <button
            onClick={() => setActiveTab('compose')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'compose'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Compose
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'settings'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Settings
          </button>
        </nav>
      </div>

      <div className="py-6">
        {activeTab === 'feed' && renderAlertFeed()}
        {activeTab === 'compose' && renderCompose()}
        {activeTab === 'settings' && renderSettings()}
      </div>
    </div>
  );
}