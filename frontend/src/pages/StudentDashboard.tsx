import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Bell, Calendar, FileText, BookOpen, Clock, CheckCircle2, AlertCircle, LogOut, GraduationCap, Download, FileJson, FileSpreadsheet, PlayCircle, ExternalLink, X, Plus, FileCheck, ChevronRight, RefreshCw } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useCourses, useAnnouncements } from '@/hooks/useCourses';
import { getWebSocketUrl } from '@/utils/websocket';

interface StudentAlert {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

interface CourseDisplay {
  id: string;
  name: string;
  instructor: string;
  nextClass: string;
  assignments: number;
  description?: string;
  ploneUrl?: string;
  lastUpdated?: string;
  progress?: number;
}

interface ScheduleEvent {
  id: string;
  title: string;
  course: string;
  type: 'lecture' | 'lab' | 'exam' | 'assignment';
  date: string;
  time: string;
  location: string;
  importedAt?: string;
}

interface MediaResource {
  id: string;
  title: string;
  description: string;
  course: string;
  type: 'video' | 'slides' | 'document';
  url: string;
  embedUrl?: string;
  thumbnail?: string;
  duration?: string;
  uploadedBy: string;
  uploadedAt: string;
}

interface WorkflowRequest {
  id: string;
  title: string;
  type: 'course-add' | 'course-drop' | 'grade-appeal' | 'extension-request';
  status: 'pending' | 'approved' | 'rejected' | 'in-review';
  submittedAt: string;
  course?: string;
  reason?: string;
  reviewedBy?: string;
  reviewedAt?: string;
  comments?: string;
}

export function StudentDashboard() {
  const { user } = useAuth();
  const { data: courses, isLoading: coursesLoading, error: coursesError, refetch: refetchCourses } = useCourses();
  const { data: announcements, isLoading: announcementsLoading, refetch: refetchAnnouncements } = useAnnouncements();
  const [alerts, setAlerts] = useState<StudentAlert[]>([
    {
      id: '1',
      type: 'info',
      title: 'Welcome to Spring 2025!',
      message: 'Classes begin on January 20th. Make sure to check your schedule.',
      timestamp: '1 hour ago',
      read: false
    },
    {
      id: '2',
      type: 'warning',
      title: 'Assignment Due Soon',
      message: 'Physics Lab Report due in 2 days',
      timestamp: '3 hours ago',
      read: false
    }
  ]);

  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportFormat, setExportFormat] = useState<'json' | 'csv' | 'pdf'>('json');
  const [apiUsage, setApiUsage] = useState({ used: 3, limit: 10 });
  const [selectedVideo, setSelectedVideo] = useState<MediaResource | null>(null);
  const [showWorkflowModal, setShowWorkflowModal] = useState(false);
  const [workflowType, setWorkflowType] = useState<'course-add' | 'course-drop'>('course-add');
  const [workflowRequests, setWorkflowRequests] = useState<WorkflowRequest[]>([
    {
      id: '1',
      title: 'Drop Physics Lab',
      type: 'course-drop',
      status: 'approved',
      submittedAt: '3 days ago',
      course: 'Physics Lab',
      reason: 'Schedule conflict with internship',
      reviewedBy: 'Academic Advisor',
      reviewedAt: '2 days ago',
      comments: 'Approved. Please ensure you complete this course next semester.'
    },
    {
      id: '2',
      title: 'Add Advanced Database Systems',
      type: 'course-add',
      status: 'pending',
      submittedAt: '1 hour ago',
      course: 'CS 302',
      reason: 'Prerequisite completed with A grade, ready for advanced course'
    }
  ]);
  const [schedule, setSchedule] = useState<ScheduleEvent[]>([
    {
      id: '1',
      title: 'Introduction to Algorithms',
      course: 'CS 101',
      type: 'lecture',
      date: 'Today',
      time: '2:00 PM',
      location: 'Room 301',
      importedAt: '10 minutes ago'
    },
    {
      id: '2',
      title: 'Physics Lab Session',
      course: 'Physics Lab',
      type: 'lab',
      date: 'Tomorrow',
      time: '9:00 AM',
      location: 'Lab Building A',
      importedAt: '10 minutes ago'
    },
    {
      id: '3',
      title: 'Midterm Exam',
      course: 'Math 201',
      type: 'exam',
      date: 'Friday',
      time: '10:00 AM',
      location: 'Exam Hall 1',
      importedAt: '10 minutes ago'
    }
  ]);

  // Extract media resources from courses
  const mediaResources: MediaResource[] = React.useMemo(() => {
    // First, try to get resources from courses if available
    const resources: MediaResource[] = [];
    
    if (courses && courses.length > 0) {
      courses.forEach(course => {
        course.resources?.forEach(resource => {
          if (resource.type === 'video' && resource.embedUrl) {
            resources.push({
              id: resource.id,
              title: resource.title,
              description: resource.description,
              course: course.title,
              type: 'video',
              url: resource.url,
              embedUrl: resource.embedUrl,
              thumbnail: resource.embedUrl?.includes('youtube') 
                ? `https://i.ytimg.com/vi/${resource.embedUrl.split('/').pop()}/maxresdefault.jpg`
                : undefined,
              duration: resource.duration,
              uploadedBy: resource.instructor || course.instructor,
              uploadedAt: '1 day ago' // This would come from Plone
            });
          }
        });
      });
    }
    
    // If no resources from Plone or courses not loaded, show some defaults
    if (resources.length === 0) {
      return [
        {
          id: '1',
          title: 'Binary Search Trees - Complete Guide',
          description: 'Comprehensive lecture covering BST operations, balancing, and real-world applications',
          course: 'Computer Science 101',
          type: 'video',
          url: 'https://www.youtube.com/watch?v=JfSdGQdAzq8',
          embedUrl: 'https://www.youtube.com/embed/JfSdGQdAzq8',
          thumbnail: 'https://i.ytimg.com/vi/JfSdGQdAzq8/maxresdefault.jpg',
          duration: '45:23',
          uploadedBy: 'Dr. Smith',
          uploadedAt: '2 days ago'
        },
        {
          id: '2',
          title: 'Quantum Mechanics Lab Preparation',
          description: 'Pre-lab video explaining double-slit experiment setup and wave-particle duality concepts',
          course: 'Physics Lab',
          type: 'video',
          url: 'https://www.youtube.com/watch?v=Iuv6hY6zsd0',
          embedUrl: 'https://www.youtube.com/embed/Iuv6hY6zsd0',
          thumbnail: 'https://i.ytimg.com/vi/Iuv6hY6zsd0/maxresdefault.jpg',
          duration: '9:08',
          uploadedBy: 'Prof. Johnson',
          uploadedAt: '1 day ago'
        },
        {
          id: '3',
          title: 'Linear Algebra Review Session',
          description: 'Complete review of eigenvalues and eigenvectors for the upcoming midterm',
          course: 'Mathematics 201',
          type: 'video',
          url: 'https://www.youtube.com/watch?v=PFDu9oVAE-g',
          embedUrl: 'https://www.youtube.com/embed/PFDu9oVAE-g',
          thumbnail: 'https://i.ytimg.com/vi/PFDu9oVAE-g/maxresdefault.jpg',
          duration: '58:14',
          uploadedBy: 'Dr. Chen',
          uploadedAt: '3 hours ago'
        }
      ];
    }
    
    return resources;
  }, [courses]);

  // Connect to WebSocket for real-time alerts
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      setWsStatus('connecting');
      const websocket = new WebSocket(getWebSocketUrl('/alerts/ws'));
      
      websocket.onopen = () => {
        console.log('WebSocket connected');
        setWsStatus('connected');
      };
      
      websocket.onmessage = (event) => {
        try {
          const alert = JSON.parse(event.data);
          console.log('Received alert:', alert);
          
          // Add new alert to the list
          // Map priority levels to alert types for display
          const typeMap: { [key: string]: StudentAlert['type'] } = {
            'low': 'info',
            'medium': 'info',
            'high': 'warning',
            'critical': 'error'
          };
          
          const newAlert: StudentAlert = {
            id: alert.id || Date.now().toString(),
            type: typeMap[alert.priority] || alert.type || 'info',
            title: alert.title,
            message: alert.message,
            timestamp: 'just now',
            read: false
          };
          
          // Prevent duplicate alerts
          setAlerts(prev => {
            if (prev.some(a => a.id === newAlert.id)) {
              console.log('Duplicate alert ignored:', newAlert.id);
              return prev;
            }
            return [newAlert, ...prev];
          });
        } catch (error) {
          console.error('Failed to parse alert:', error);
        }
      };
      
      websocket.onclose = () => {
        console.log('WebSocket disconnected');
        setWsStatus('disconnected');
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsStatus('disconnected');
      };
      
      setWs(websocket);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setWsStatus('disconnected');
    }
  };

  // Convert API courses to display format
  const displayCourses: CourseDisplay[] = courses?.map(course => ({
    id: course.id,
    name: course.title,
    instructor: course.instructor,
    nextClass: 'See schedule', // This would come from schedule data
    assignments: course.resources?.filter(r => r.type === 'assignment').length || 0,
    description: course.description,
    ploneUrl: `/Plone/courses/${course.id}`,
    lastUpdated: '2 hours ago', // This would come from Plone modified date
    progress: course.progress
  })) || [];

  const markAsRead = (alertId: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, read: true } : alert
    ));
  };

  const getAlertIcon = (type: StudentAlert['type']) => {
    switch (type) {
      case 'success': return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'warning': return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'error': return <AlertCircle className="h-5 w-5 text-red-500" />;
      default: return <Bell className="h-5 w-5 text-blue-500" />;
    }
  };

  const handleExport = async (format: 'json' | 'csv' | 'pdf') => {
    // Simulate API call and rate limit update
    setApiUsage(prev => ({ ...prev, used: prev.used + 1 }));
    
    // Create sample data
    const studentData = {
      student: {
        id: 'STU-2025-001',
        name: user?.name || user?.email?.split('@')[0],
        email: user?.email,
        enrollment: 'Spring 2025'
      },
      courses: displayCourses,
      schedule: schedule,
      alerts: alerts.slice(0, 5) // Last 5 alerts
    };

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(studentData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `student-data-${Date.now()}.json`;
      a.click();
    } else if (format === 'csv') {
      // Simple CSV generation
      const csv = `Course,Instructor,Next Class,Assignments\n${displayCourses.map(c => 
        `"${c.name}","${c.instructor}","${c.nextClass}",${c.assignments}`
      ).join('\n')}`;
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `courses-${Date.now()}.csv`;
      a.click();
    } else {
      alert('PDF export would generate a formatted report');
    }
    
    setShowExportModal(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Student Header Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <GraduationCap className="h-8 w-8" />
                <span>STUDENT PORTAL</span>
              </h1>
              <p className="mt-2 text-blue-100">
                Logged in as: <span className="font-semibold">{user?.email}</span>
              </p>
            </div>
            <div className="text-right">
              <span className="bg-white/20 px-3 py-1 rounded-md text-sm uppercase tracking-wider">
                Student ID: STU-2025-001
              </span>
              <p className="text-xs text-blue-200 mt-2">Spring 2025 Enrollment</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Welcome Section */}
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Dashboard Overview</h2>
            <p className="mt-1 text-gray-600">
              Welcome back, {user?.name || user?.email?.split('@')[0]}! Here's your academic overview.
            </p>
          </div>
          <button
            onClick={async () => {
              const response = await fetch('/auth/logout', { method: 'POST', credentials: 'include' });
              if (response.ok) {
                window.location.href = '/';
              }
            }}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors shadow-sm"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Enrolled Courses</p>
              <p className="text-2xl font-bold text-gray-900">{displayCourses.length}</p>
            </div>
            <BookOpen className="h-8 w-8 text-blue-500" />
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending Assignments</p>
              <p className="text-2xl font-bold text-gray-900">3</p>
            </div>
            <FileText className="h-8 w-8 text-orange-500" />
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Unread Alerts</p>
              <p className="text-2xl font-bold text-gray-900">{alerts.filter(a => !a.read).length + (announcements?.length || 0)}</p>
            </div>
            <Bell className="h-8 w-8 text-red-500" />
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Next Class</p>
              <p className="text-lg font-bold text-gray-900">9:00 AM</p>
            </div>
            <Clock className="h-8 w-8 text-purple-500" />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alerts Section with Plone Announcements */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Recent Alerts & Announcements</h2>
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
          
          <div className="space-y-3">
            {/* Show Plone announcements first */}
            {announcements && announcements.map((announcement) => (
              <Card 
                key={`announce-${announcement.id}`} 
                className="p-4 bg-blue-50/50 border-blue-300"
              >
                <div className="flex items-start gap-3">
                  {announcement.type === 'success' ? <CheckCircle2 className="h-5 w-5 text-green-500" /> :
                   announcement.type === 'warning' ? <AlertCircle className="h-5 w-5 text-yellow-500" /> :
                   <Bell className="h-5 w-5 text-blue-500" />}
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">
                      {announcement.title}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">{announcement.content}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      {announcement.author ? `By ${announcement.author} • ` : ''}
                      {new Date(announcement.created).toLocaleDateString()}
                    </p>
                  </div>
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">Plone</span>
                </div>
              </Card>
            ))}
            
            {/* Then show WebSocket alerts */}
            {alerts.length === 0 && (!announcements || announcements.length === 0) ? (
              <Card className="p-6 text-center">
                <Bell className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600">No alerts yet</p>
              </Card>
            ) : (
              alerts.map((alert) => (
                <Card 
                  key={alert.id} 
                  className={`p-4 cursor-pointer transition-all ${!alert.read ? 'bg-blue-50/50 border-blue-300' : ''}`}
                  onClick={() => markAsRead(alert.id)}
                >
                  <div className="flex items-start gap-3">
                    {getAlertIcon(alert.type)}
                    <div className="flex-1">
                      <h3 className={`font-medium ${!alert.read ? 'text-gray-900' : 'text-gray-700'}`}>
                        {alert.title}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                      <p className="text-xs text-gray-500 mt-2">{alert.timestamp}</p>
                    </div>
                    {!alert.read && (
                      <span className="w-2 h-2 bg-blue-500 rounded-full mt-1"></span>
                    )}
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>

        {/* Courses Section with Plone Integration */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">My Courses</h2>
            <span className="text-sm text-gray-500 flex items-center gap-1">
              <Clock className="h-4 w-4" />
              Synced with Plone CMS
            </span>
          </div>
          <div className="space-y-3">
            {displayCourses.map((course) => (
              <Card key={course.id} className="p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-gray-900">{course.name}</h3>
                      {course.lastUpdated === 'just updated' && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Updated
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{course.description}</p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      <span>Instructor: {course.instructor}</span>
                      <span>•</span>
                      <span>Next class: {course.nextClass}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                      <button className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1">
                        <BookOpen className="h-3 w-3" />
                        View in Plone
                      </button>
                      <span className="text-xs text-gray-400">•</span>
                      <span className="text-xs text-gray-500">Last updated: {course.lastUpdated}</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    {course.assignments > 0 && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                        {course.assignments} due
                      </span>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Schedule Section - Shows CSV Import Results */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">My Schedule</h2>
          <div className="flex items-center gap-3">
            {schedule.length > 0 && schedule[0].importedAt && (
              <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Schedule updated {schedule[0].importedAt}
              </span>
            )}
            <button className="text-sm text-blue-600 hover:text-blue-700">
              View Full Calendar
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {schedule.map((event) => {
            const typeColors = {
              lecture: 'bg-blue-50 border-blue-200 text-blue-700',
              lab: 'bg-purple-50 border-purple-200 text-purple-700',
              exam: 'bg-red-50 border-red-200 text-red-700',
              assignment: 'bg-orange-50 border-orange-200 text-orange-700'
            };
            
            const typeIcons = {
              lecture: BookOpen,
              lab: FileText,
              exam: AlertCircle,
              assignment: FileText
            };
            
            const Icon = typeIcons[event.type];
            
            return (
              <Card key={event.id} className={`p-4 border-2 ${typeColors[event.type]}`}>
                <div className="flex items-start gap-3">
                  <Icon className={`h-5 w-5 mt-0.5 ${typeColors[event.type].split(' ')[2]}`} />
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{event.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{event.course}</p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                      <Calendar className="h-3 w-3" />
                      <span>{event.date} at {event.time}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                      <Clock className="h-3 w-3" />
                      <span>{event.location}</span>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Workflow Requests Section - Phase 7 */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Academic Requests</h2>
          <button
            onClick={() => setShowWorkflowModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            New Request
          </button>
        </div>
        
        <div className="space-y-3">
          {workflowRequests.map((request) => {
            const statusColors = {
              pending: 'bg-yellow-50 text-yellow-700 border-yellow-200',
              approved: 'bg-green-50 text-green-700 border-green-200',
              rejected: 'bg-red-50 text-red-700 border-red-200',
              'in-review': 'bg-blue-50 text-blue-700 border-blue-200'
            };
            
            return (
              <Card key={request.id} className="p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <FileCheck className="h-5 w-5 text-gray-400" />
                      <h3 className="font-medium text-gray-900">{request.title}</h3>
                      <span className={`px-2 py-1 text-xs rounded-full border ${statusColors[request.status]}`}>
                        {request.status.charAt(0).toUpperCase() + request.status.slice(1).replace('-', ' ')}
                      </span>
                    </div>
                    {request.course && (
                      <p className="text-sm text-gray-600 mt-1 ml-8">Course: {request.course}</p>
                    )}
                    <p className="text-sm text-gray-500 mt-1 ml-8">{request.reason}</p>
                    {request.comments && (
                      <div className="mt-2 ml-8 p-2 bg-gray-50 rounded text-sm text-gray-700">
                        <strong>Admin response:</strong> {request.comments}
                      </div>
                    )}
                    <div className="flex items-center gap-4 mt-2 ml-8 text-xs text-gray-500">
                      <span>Submitted {request.submittedAt}</span>
                      {request.reviewedAt && (
                        <span>Reviewed {request.reviewedAt} by {request.reviewedBy}</span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                </div>
              </Card>
            );
          })}
        </div>
        
        <div className="mt-4 text-center">
          <button className="text-sm text-blue-600 hover:text-blue-700">
            View all requests
          </button>
        </div>
      </div>

      {/* Quick Actions for Students */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all">
            <Calendar className="h-6 w-6 text-gray-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-700">View Schedule</p>
          </button>
          <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-400 hover:bg-green-50 transition-all">
            <FileText className="h-6 w-6 text-gray-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-700">Submit Assignment</p>
          </button>
          <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-all">
            <BookOpen className="h-6 w-6 text-gray-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-700">Course Materials</p>
          </button>
          <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-orange-400 hover:bg-orange-50 transition-all">
            <Bell className="h-6 w-6 text-gray-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-700">Notification Settings</p>
          </button>
        </div>
      </div>

      {/* Media Resources Section - Phase 5 */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Course Media Resources</h2>
          <span className="text-sm text-gray-500 flex items-center gap-1">
            <PlayCircle className="h-4 w-4" />
            Rich media via oEmbed
          </span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {mediaResources.map((resource) => (
            <Card 
              key={resource.id} 
              className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => setSelectedVideo(resource)}
            >
              <div className="relative">
                <img 
                  src={resource.thumbnail} 
                  alt={resource.title}
                  className="w-full h-48 object-cover"
                />
                <div className="absolute inset-0 bg-black bg-opacity-30 flex items-center justify-center">
                  <PlayCircle className="h-12 w-12 text-white" />
                </div>
                {resource.duration && (
                  <span className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                    {resource.duration}
                  </span>
                )}
              </div>
              <div className="p-4">
                <h3 className="font-medium text-gray-900 line-clamp-2">{resource.title}</h3>
                <p className="text-sm text-gray-600 mt-1">{resource.course}</p>
                <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                  <span>{resource.uploadedBy}</span>
                  <span>{resource.uploadedAt}</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
        
        <div className="mt-4 flex justify-center">
          <button className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
            View all media resources
            <ExternalLink className="h-3 w-3" />
          </button>
        </div>
      </div>

      {/* Export My Data Section - Phase 6 */}
      <div className="mt-8">
        <Card className="p-6 bg-gradient-to-br from-gray-50 to-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Download className="h-5 w-5" />
                Export My Data
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Download your academic data in various formats. Part of our open data initiative.
              </p>
              <div className="mt-4 flex items-center gap-4">
                <button
                  onClick={() => setShowExportModal(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
                >
                  Export Data
                </button>
                <span className="text-sm text-gray-500">
                  API Usage: {apiUsage.used}/{apiUsage.limit} requests today
                </span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">Phase 6 Feature</p>
              <p className="text-xs text-gray-400 mt-1">Open Data API</p>
            </div>
          </div>
        </Card>
      </div>
      </div>

      {/* Video Player Modal */}
      {selectedVideo && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-4xl">
            <div className="p-4 border-b flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{selectedVideo.title}</h3>
                <p className="text-sm text-gray-600 mt-1">{selectedVideo.course}</p>
              </div>
              <button
                onClick={() => setSelectedVideo(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            <div className="aspect-video bg-black">
              <iframe
                src={selectedVideo.embedUrl}
                title={selectedVideo.title}
                className="w-full h-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
            <div className="p-4">
              <p className="text-sm text-gray-700">{selectedVideo.description}</p>
              <div className="flex items-center justify-between mt-4 text-sm text-gray-500">
                <span>Uploaded by {selectedVideo.uploadedBy}</span>
                <span>{selectedVideo.uploadedAt}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Request Modal */}
      {showWorkflowModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Submit Academic Request</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Request Type
                  </label>
                  <select
                    value={workflowType}
                    onChange={(e) => setWorkflowType(e.target.value as any)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="course-add">Add Course</option>
                    <option value="course-drop">Drop Course</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Course
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
                    <option>CS 302 - Advanced Database Systems</option>
                    <option>CS 303 - Machine Learning</option>
                    <option>MATH 301 - Abstract Algebra</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reason
                  </label>
                  <textarea
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="Please explain your reason for this request..."
                  />
                </div>
              </div>
              
              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={() => setShowWorkflowModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={async () => {
                    // Send alert to admin
                    try {
                      await fetch('/alerts/send', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({
                          title: 'New Workflow Request',
                          message: 'Student has submitted a course add/drop request requiring approval',
                          priority: 'high',
                          category: 'workflow',
                          channels: ['websocket']
                        })
                      });
                    } catch (error) {
                      console.error('Failed to send workflow alert:', error);
                    }
                    
                    // Add to local list
                    setWorkflowRequests(prev => [{
                      id: Date.now().toString(),
                      title: workflowType === 'course-add' ? 'Add CS 302' : 'Drop CS 302',
                      type: workflowType,
                      status: 'pending',
                      submittedAt: 'just now',
                      course: 'CS 302',
                      reason: 'Submitted via demo'
                    }, ...prev]);
                    
                    setShowWorkflowModal(false);
                    alert('Request submitted successfully!');
                  }}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                >
                  Submit Request
                </button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Your Data</h3>
              <p className="text-sm text-gray-600 mb-6">
                Choose a format to export your academic data. This will include your courses, schedule, and recent alerts.
              </p>
              
              <div className="space-y-3">
                <button
                  onClick={() => handleExport('json')}
                  className="w-full p-4 border rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all text-left group"
                >
                  <div className="flex items-center gap-3">
                    <FileJson className="h-8 w-8 text-blue-600" />
                    <div>
                      <p className="font-medium text-gray-900">JSON Format</p>
                      <p className="text-sm text-gray-500">Machine-readable format for developers</p>
                    </div>
                  </div>
                </button>
                
                <button
                  onClick={() => handleExport('csv')}
                  className="w-full p-4 border rounded-lg hover:border-green-400 hover:bg-green-50 transition-all text-left group"
                >
                  <div className="flex items-center gap-3">
                    <FileSpreadsheet className="h-8 w-8 text-green-600" />
                    <div>
                      <p className="font-medium text-gray-900">CSV Format</p>
                      <p className="text-sm text-gray-500">Open in Excel or Google Sheets</p>
                    </div>
                  </div>
                </button>
                
                <button
                  onClick={() => handleExport('pdf')}
                  className="w-full p-4 border rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-all text-left group"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-8 w-8 text-purple-600" />
                    <div>
                      <p className="font-medium text-gray-900">PDF Report</p>
                      <p className="text-sm text-gray-500">Formatted document for printing</p>
                    </div>
                  </div>
                </button>
              </div>
              
              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={() => setShowExportModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}