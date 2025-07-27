import React, { useState } from 'react';
import { Card } from '@/components/ui/card';

interface EmbedData {
  html: string;
  title?: string;
  provider_name?: string;
  thumbnail_url?: string;
}

export function EmbedPreview() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [embedData, setEmbedData] = useState<EmbedData | null>(null);
  const [rawResponse, setRawResponse] = useState<string | null>(null);

  const handlePreview = async () => {
    if (!url) {
      setError('Please enter a URL');
      return;
    }

    setLoading(true);
    setError(null);
    setEmbedData(null);
    setRawResponse(null);

    try {
      const response = await fetch(`/oembed/?url=${encodeURIComponent(url)}`, {
        credentials: 'include',
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch embed');
      }

      setEmbedData(data);
      setRawResponse(JSON.stringify(data, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to preview embed');
    } finally {
      setLoading(false);
    }
  };

  const testUrls = [
    { label: 'YouTube Video', url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' },
    { label: 'Twitter/X Post', url: 'https://x.com/Ryan26295/status/1939485261571735743' },
    { label: 'Vimeo Video', url: 'https://vimeo.com/1234567' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Rich Media Embeds (oEmbed)</h1>
        <p className="mt-2 text-gray-600">
          Preview how URLs will be embedded in your content using oEmbed providers.
        </p>
      </div>

      <Card>
        <div className="space-y-4">
          <div>
            <label htmlFor="url" className="block text-sm font-medium text-gray-700">
              Media URL
            </label>
            <div className="mt-1 flex gap-2">
              <input
                type="url"
                id="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handlePreview}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-400"
              >
                {loading ? 'Loading...' : 'Preview'}
              </button>
            </div>
          </div>

          <div className="border-t pt-4">
            <p className="text-sm font-medium text-gray-700 mb-2">Quick Test URLs:</p>
            <div className="flex flex-wrap gap-2">
              {testUrls.map((test) => (
                <button
                  key={test.label}
                  onClick={() => setUrl(test.url)}
                  className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition"
                >
                  {test.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <div className="flex items-center gap-2 text-red-700">
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="font-medium">Error:</span>
            <span>{error}</span>
          </div>
        </Card>
      )}

      {embedData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Preview</h3>
            <div className="prose max-w-none">
              {embedData.html ? (
                <div 
                  dangerouslySetInnerHTML={{ __html: embedData.html }}
                  className="embed-container"
                />
              ) : (
                <p className="text-gray-500">No HTML preview available</p>
              )}
            </div>
            {embedData.title && (
              <div className="mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Title:</span> {embedData.title}
                </p>
                {embedData.provider_name && (
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Provider:</span> {embedData.provider_name}
                  </p>
                )}
              </div>
            )}
          </Card>

          <Card>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Raw Response</h3>
            <pre className="bg-gray-50 p-4 rounded-md overflow-auto text-sm">
              {rawResponse}
            </pre>
          </Card>
        </div>
      )}

      <Card className="bg-blue-50 border-blue-200">
        <h3 className="text-lg font-medium text-blue-900 mb-2">How it works</h3>
        <ul className="space-y-2 text-sm text-blue-800">
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-0.5">•</span>
            <span>Enter a URL from a supported provider (YouTube, Vimeo, Twitter, etc.)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-0.5">•</span>
            <span>The backend fetches embed data from the provider's oEmbed endpoint</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-0.5">•</span>
            <span>Responses are cached to improve performance</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 mt-0.5">•</span>
            <span>HTML is sanitized for security before display</span>
          </li>
        </ul>
      </Card>
    </div>
  );
}