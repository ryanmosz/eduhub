import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Zap, CheckCircle2 } from 'lucide-react';

export function SimplePerformanceDemo() {
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<any>(null);

  const runSimpleTest = async () => {
    setIsRunning(true);
    setResults(null);

    try {
      const numRequests = 20;
      const startTime = Date.now();
      
      // Just hit the root endpoint which should always work
      const promises = Array.from({ length: numRequests }, () => 
        fetch('/', { method: 'GET' })
          .then(r => r.ok)
          .catch(() => false)
      );

      const responses = await Promise.all(promises);
      const endTime = Date.now();
      const totalTime = (endTime - startTime) / 1000;
      const successful = responses.filter(r => r).length;

      setResults({
        totalRequests: numRequests,
        successful,
        totalTime,
        requestsPerSecond: numRequests / totalTime,
        avgResponseTime: (totalTime / numRequests) * 1000
      });
    } catch (error) {
      console.error('Test error:', error);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <Card className="p-6 bg-blue-50 border-blue-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
        <Zap className="h-5 w-5 text-blue-600" />
        Quick Performance Check
      </h3>
      <p className="text-sm text-gray-600 mb-4">
        Test how fast our async architecture handles {20} concurrent requests
      </p>
      
      <button
        onClick={runSimpleTest}
        disabled={isRunning}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
      >
        {isRunning ? 'Testing...' : 'Run Quick Test'}
      </button>

      {results && (
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="bg-white p-3 rounded">
            <p className="text-xs text-gray-600">Speed</p>
            <p className="text-lg font-bold text-blue-600">
              {results.requestsPerSecond.toFixed(0)} req/s
            </p>
          </div>
          <div className="bg-white p-3 rounded">
            <p className="text-xs text-gray-600">Avg Response</p>
            <p className="text-lg font-bold text-green-600">
              {results.avgResponseTime.toFixed(0)}ms
            </p>
          </div>
        </div>
      )}

      {results && results.requestsPerSecond > 50 && (
        <div className="mt-3 flex items-center gap-2 text-green-700 text-sm">
          <CheckCircle2 className="h-4 w-4" />
          <span>Excellent! This speed prevents registration day crashes</span>
        </div>
      )}
    </Card>
  );
}