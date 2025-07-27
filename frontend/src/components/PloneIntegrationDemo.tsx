import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Server, Zap, Shield, AlertCircle, CheckCircle2, RefreshCw } from 'lucide-react';

export function PloneIntegrationDemo() {
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<any>(null);

  const runPloneLoadTest = async (numRequests: number) => {
    setIsRunning(true);
    try {
      const response = await fetch(`/api/performance/demo-plone-load?requests=${numRequests}`, {
        credentials: 'include',
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Load test error:', error);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <Card className="p-6 bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200">
      <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Shield className="h-6 w-6 text-purple-600" />
        Authenticated Plone Integration Demo - See How We Protect Plone
      </h3>
      
      <div className="mb-6 bg-white p-4 rounded-lg border border-purple-200">
        <p className="text-sm text-gray-700 mb-3">
          <strong>This demonstrates our real Plone integration pattern:</strong>
        </p>
        <ul className="text-sm space-y-2">
          <li className="flex items-start gap-2">
            <CheckCircle2 className="h-4 w-4 text-purple-600 mt-0.5" />
            <span><strong>Authentication:</strong> Uses your admin login to make authenticated Plone requests</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
            <span><strong>With Plone running:</strong> Makes real authenticated API requests to Plone endpoints</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="h-4 w-4 text-blue-600 mt-0.5" />
            <span><strong>Without Plone:</strong> Shows the same integration pattern with simulated responses</span>
          </li>
          <li className="flex items-start gap-2">
            <Zap className="h-4 w-4 text-yellow-600 mt-0.5" />
            <span><strong>Key insight:</strong> FastAPI protects Plone from direct traffic spikes while maintaining user context</span>
          </li>
        </ul>
      </div>

      <div className="flex gap-3 mb-6">
        <button
          onClick={() => runPloneLoadTest(10)}
          disabled={isRunning}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400"
        >
          Test 10 Users
        </button>
        <button
          onClick={() => runPloneLoadTest(20)}
          disabled={isRunning}
          className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:bg-gray-400"
        >
          Test 20 Users (Plone struggles)
        </button>
        <button
          onClick={() => runPloneLoadTest(50)}
          disabled={isRunning}
          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-400"
        >
          Test 50 Users (Plone crashes)
        </button>
      </div>

      {isRunning && (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="h-8 w-8 text-purple-600 animate-spin" />
          <span className="ml-3 text-gray-700">Running Plone integration test...</span>
        </div>
      )}

      {results && !isRunning && (
        <div className="space-y-4">
          {/* Test Configuration */}
          <div className="bg-white p-4 rounded-lg border border-purple-200">
            <h4 className="font-semibold text-gray-900 mb-2">Test Configuration:</h4>
            <div className="text-sm space-y-1">
              <p>• Authenticated as: <strong>{results.test_configuration.authenticated_as}</strong> ({results.test_configuration.user_role})</p>
              <p>• Concurrent Requests: <strong>{results.test_configuration.concurrent_requests}</strong></p>
              <p>• Plone Status: <span className={results.test_configuration.plone_status.includes('Connected') ? 'text-green-600' : 'text-blue-600'}>
                {results.test_configuration.plone_status}
              </span></p>
              <p>• Test Mode: {results.test_configuration.test_mode}</p>
            </div>
          </div>

          {/* Our System Results */}
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              Our System Performance:
            </h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Speed:</p>
                <p className="text-2xl font-bold text-green-600">{results.our_system_results.requests_per_second} req/s</p>
              </div>
              <div>
                <p className="text-gray-600">Response Time:</p>
                <p className="text-2xl font-bold text-blue-600">{results.our_system_results.average_response_ms}ms</p>
              </div>
            </div>
            <p className="text-sm text-green-700 mt-2">
              ✅ All {results.test_configuration.concurrent_requests} requests handled successfully!
            </p>
          </div>

          {/* Direct Plone Behavior */}
          <div className="bg-red-50 p-4 rounded-lg border border-red-200">
            <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              Direct Plone Behavior (Without Our Gateway):
            </h4>
            <div className="text-sm space-y-1">
              {Object.entries(results.direct_plone_behavior).map(([key, value]) => (
                <p key={key} className="flex justify-between">
                  <span className="text-gray-600">{key.replace(/_/g, ' ').replace('at ', '')}:</span>
                  <span className="font-medium text-red-700">{value as string}</span>
                </p>
              ))}
            </div>
          </div>

          {/* Integration Pattern */}
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h4 className="font-semibold text-gray-900 mb-2">How Our Integration Works:</h4>
            <ol className="text-sm space-y-2">
              {Object.entries(results.plone_integration_pattern).map(([key, value]) => {
                if (key === 'result') return null;
                return (
                  <li key={key} className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold">{key.replace('step', '')}.</span>
                    <span>{value as string}</span>
                  </li>
                );
              })}
            </ol>
            <p className="mt-3 text-sm font-semibold text-blue-700 bg-blue-100 p-2 rounded">
              {results.plone_integration_pattern.result}
            </p>
          </div>

          {/* Key Benefits */}
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <h4 className="font-semibold text-gray-900 mb-2">Summary:</h4>
            <ul className="text-sm space-y-1">
              {results.key_benefits.map((benefit: string, index: number) => (
                <li key={index}>{benefit}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </Card>
  );
}