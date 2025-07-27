import React from 'react';
import { SimplePerformanceDemo } from '@/components/SimplePerformanceDemo';
import { FullPerformanceDemo } from '@/components/FullPerformanceDemo';
import { PloneIntegrationDemo } from '@/components/PloneIntegrationDemo';
import { Card } from '@/components/ui/card';
import { Zap, Clock, Users, AlertCircle, CheckCircle2, Activity, Server, Layers } from 'lucide-react';

export function PerformanceDemo() {
  const [ploneStatus, setPloneStatus] = React.useState<any>(null);
  const [checkingPlone, setCheckingPlone] = React.useState(false);

  const checkPloneConnection = async () => {
    setCheckingPlone(true);
    try {
      const response = await fetch('/api/performance/plone-integration-demo', {
        credentials: 'include',
      });
      const data = await response.json();
      setPloneStatus(data);
    } catch (error) {
      console.error('Failed to check Plone status:', error);
    } finally {
      setCheckingPlone(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Python 3.11 + Async Performance</h1>
        <p className="mt-2 text-gray-600">
          See how our modern architecture solves the concurrent user problem
        </p>
      </div>

      {/* The Problem */}
      <Card className="p-6 bg-red-50 border-red-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <AlertCircle className="h-6 w-6 text-red-600" />
          The Problem: Registration Day Crashes
        </h2>
        <blockquote className="italic text-gray-700 border-l-4 border-red-400 pl-4">
          "When our Spring schedule goes live at 8 AM, students and parents hit refresh constantly. 
          The old system would crash within minutes, forcing me to spend my morning fielding angry 
          calls instead of handling real emergencies."
          <footer className="text-sm mt-2">— Program Operations Manager, Metro Community College</footer>
        </blockquote>
      </Card>

      {/* Plone Connection Status */}
      <Card className="p-6 bg-purple-50 border-purple-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Server className="h-6 w-6 text-purple-600" />
          Plone Integration Status
        </h2>
        
        <button
          onClick={checkPloneConnection}
          disabled={checkingPlone}
          className="mb-4 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400"
        >
          {checkingPlone ? 'Checking...' : 'Check Plone Connection'}
        </button>

        {ploneStatus && (
          <div className="space-y-4">
            {/* Live Status */}
            <div className="bg-white p-4 rounded-lg border border-purple-200">
              <h3 className="font-semibold mb-2">Live Plone Status:</h3>
              {ploneStatus.live_plone_status.connected ? (
                <div className="text-green-700">
                  <p>✅ Connected to Plone</p>
                  <p className="text-sm mt-1">Version: {ploneStatus.live_plone_status.plone_version}</p>
                  <p className="text-sm">Response time: {ploneStatus.live_plone_status.response_time_ms}ms</p>
                  <p className="text-sm">URL: {ploneStatus.live_plone_status.api_url}</p>
                </div>
              ) : (
                <div className="text-red-700">
                  <p>❌ Plone not connected</p>
                  <p className="text-sm mt-1">{ploneStatus.live_plone_status.error}</p>
                  <p className="text-sm text-blue-600 mt-2">{ploneStatus.live_plone_status.note}</p>
                </div>
              )}
            </div>

            {/* Architecture Flow */}
            <div className="bg-white p-4 rounded-lg border border-purple-200">
              <h3 className="font-semibold mb-2">Current Architecture:</h3>
              <p className="text-sm font-mono bg-gray-100 p-2 rounded">
                {ploneStatus.current_architecture.data_flow}
              </p>
            </div>
          </div>
        )}
      </Card>

      {/* Plone Integration Demo - THE KEY DEMO */}
      <PloneIntegrationDemo />

      {/* Quick Demo */}
      <SimplePerformanceDemo />

      {/* Full Performance Test */}
      <FullPerformanceDemo />

      {/* Architecture Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Our System */}
        <Card className="p-6 border-2 border-green-200 bg-green-50">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            EduHub with Python 3.11 + FastAPI
          </h3>
          <ul className="space-y-3 text-sm">
            <li className="flex items-start gap-2">
              <Zap className="h-4 w-4 text-green-600 mt-0.5" />
              <span><strong>Async I/O:</strong> Handles 100+ concurrent requests</span>
            </li>
            <li className="flex items-start gap-2">
              <Users className="h-4 w-4 text-green-600 mt-0.5" />
              <span><strong>Multi-user:</strong> 200+ students can register simultaneously</span>
            </li>
            <li className="flex items-start gap-2">
              <Clock className="h-4 w-4 text-green-600 mt-0.5" />
              <span><strong>Response time:</strong> Sub-100ms even under load</span>
            </li>
            <li className="flex items-start gap-2">
              <Activity className="h-4 w-4 text-green-600 mt-0.5" />
              <span><strong>Background ops:</strong> CSV imports don't block users</span>
            </li>
          </ul>
        </Card>

        {/* Legacy System */}
        <Card className="p-6 border-2 border-red-200 bg-red-50">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-600" />
            Legacy Plone (Direct Access)
          </h3>
          <ul className="space-y-3 text-sm">
            <li className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
              <span><strong>Single-threaded:</strong> Processes requests one at a time</span>
            </li>
            <li className="flex items-start gap-2">
              <Users className="h-4 w-4 text-red-600 mt-0.5" />
              <span><strong>Crashes:</strong> Dies at 20+ concurrent users</span>
            </li>
            <li className="flex items-start gap-2">
              <Clock className="h-4 w-4 text-red-600 mt-0.5" />
              <span><strong>Slow:</strong> 500ms+ response times multiply under load</span>
            </li>
            <li className="flex items-start gap-2">
              <Activity className="h-4 w-4 text-red-600 mt-0.5" />
              <span><strong>Blocking:</strong> Long operations freeze entire system</span>
            </li>
          </ul>
        </Card>
      </div>

      {/* Visual Architecture */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Layers className="h-6 w-6" />
          How It Works
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">❌ Before (Direct Plone)</h3>
            <div className="bg-gray-100 p-4 rounded font-mono text-sm">
              <div>User 1 → [Wait...] → Plone → Response</div>
              <div className="text-red-600">User 2 → [Wait for User 1...] → Plone</div>
              <div className="text-red-700">User 3 → [Wait for 1 & 2...] → 💥 Crash!</div>
            </div>
          </div>
          
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">✅ After (FastAPI + Async)</h3>
            <div className="bg-gray-100 p-4 rounded font-mono text-sm">
              <div className="text-green-600">User 1 ↘</div>
              <div className="text-green-600">User 2 → FastAPI → Plone</div>
              <div className="text-green-600">User 3 ↗</div>
              <div className="text-blue-600 mt-2">All get responses in &lt;100ms</div>
            </div>
          </div>
        </div>
      </Card>

      {/* Technical Details */}
      <Card className="p-6 bg-gray-50">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Technical Benefits</h3>
        <div className="space-y-4 text-sm">
          <div>
            <h4 className="font-semibold text-gray-900 mb-1">🚀 20-27% Performance Improvement</h4>
            <p className="text-gray-600">
              Python 3.11's optimized interpreter and better async handling provides the performance 
              headroom needed for our modernization layer.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-1">⚡ Non-blocking I/O</h4>
            <p className="text-gray-600">
              While one request waits for Plone to respond, FastAPI handles other requests. 
              This prevents the cascade failures that crash Plone during registration.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-1">🔄 Connection Pooling</h4>
            <p className="text-gray-600">
              Reuses HTTP connections to Plone instead of creating new ones for each request, 
              reducing overhead and improving response times.
            </p>
          </div>
        </div>
      </Card>

      {/* Code Examples */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Server className="h-5 w-5" />
          Where to Find It in the Code
        </h3>
        <div className="space-y-3 text-sm">
          <div className="bg-gray-100 p-3 rounded">
            <code className="text-blue-600">src/eduhub/main.py</code> - FastAPI app with async routes
          </div>
          <div className="bg-gray-100 p-3 rounded">
            <code className="text-blue-600">src/eduhub/plone_integration.py</code> - Async PloneClient with httpx
          </div>
          <div className="bg-gray-100 p-3 rounded">
            <code className="text-blue-600">src/eduhub/courses/endpoints.py</code> - Concurrent data fetching
          </div>
          <div className="bg-gray-100 p-3 rounded">
            <code className="text-blue-600">scripts/demonstrate_async_performance.py</code> - Performance testing
          </div>
        </div>
      </Card>

      {/* Impact */}
      <Card className="p-6 bg-green-50 border-green-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Real-World Impact</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <span>No more crashes during peak registration</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <span>Staff can focus on real issues, not system failures</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <span>Students get instant responses</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <span>Institution reputation protected</span>
          </div>
        </div>
      </Card>
    </div>
  );
}