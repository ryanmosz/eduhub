import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';

interface ContentItem {
  uid: string;
  title: string;
  description?: string;
  created: string;
  modified: string;
  type: string;
  public: boolean;
}

interface PaginationInfo {
  page: number;
  size: number;
  total: number;
  pages: number;
}

export function OpenDataExplorer() {
  const [activeTab, setActiveTab] = useState<'content' | 'events' | 'stats'>('content');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  
  // Data states
  const [content, setContent] = useState<ContentItem[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [stats, setStats] = useState<any>(null);

  const fetchContent = async (page: number = 1, search?: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: pageSize.toString(),
      });
      
      if (search) {
        params.append('search', search);
      }
      
      const response = await fetch(`/data/content?${params}`, {
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch content');
      }
      
      const data = await response.json();
      setContent(data.items || []);
      setPagination(data.pagination || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load content');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch('/data/categories', {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        setCategories(data.categories || []);
      }
    } catch (err) {
      console.error('Failed to fetch categories:', err);
    }
  };

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/data/stats', {
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch statistics');
      }
      
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'content') {
      fetchContent(currentPage, searchQuery);
      fetchCategories();
    } else if (activeTab === 'stats') {
      fetchStats();
    }
  }, [activeTab, currentPage]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchContent(1, searchQuery);
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (error) {
      return (
        <Card className="border-red-200 bg-red-50">
          <div className="text-red-700">
            <span className="font-medium">Error:</span> {error}
          </div>
        </Card>
      );
    }

    if (activeTab === 'content') {
      return (
        <div className="space-y-6">
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search content..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Search
            </button>
          </form>

          {categories.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <span className="text-sm font-medium text-gray-700">Categories:</span>
              {categories.map((cat) => (
                <span
                  key={cat}
                  className="px-2 py-1 text-xs bg-gray-100 rounded-full"
                >
                  {cat}
                </span>
              ))}
            </div>
          )}

          <div className="space-y-4">
            {content.length === 0 ? (
              <Card>
                <p className="text-gray-500">No content found</p>
              </Card>
            ) : (
              content.map((item) => (
                <Card key={item.uid} className="hover:shadow-md transition">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900">{item.title}</h3>
                      {item.description && (
                        <p className="mt-1 text-sm text-gray-600">{item.description}</p>
                      )}
                      <div className="mt-2 flex gap-4 text-xs text-gray-500">
                        <span>Type: {item.type}</span>
                        <span>Created: {new Date(item.created).toLocaleDateString()}</span>
                        <span>Modified: {new Date(item.modified).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      item.public ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {item.public ? 'Public' : 'Private'}
                    </span>
                  </div>
                </Card>
              ))
            )}
          </div>

          {pagination && pagination.pages > 1 && (
            <div className="flex justify-center gap-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-3 py-1 text-sm">
                Page {currentPage} of {pagination.pages}
              </span>
              <button
                onClick={() => setCurrentPage(Math.min(pagination.pages, currentPage + 1))}
                disabled={currentPage === pagination.pages}
                className="px-3 py-1 text-sm bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </div>
      );
    }

    if (activeTab === 'stats') {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {stats && (
            <>
              <Card>
                <h3 className="text-lg font-medium text-gray-900">Total Content</h3>
                <p className="mt-2 text-3xl font-bold text-blue-600">{stats.total_content || 0}</p>
              </Card>
              <Card>
                <h3 className="text-lg font-medium text-gray-900">Public Items</h3>
                <p className="mt-2 text-3xl font-bold text-green-600">{stats.public_items || 0}</p>
              </Card>
              <Card>
                <h3 className="text-lg font-medium text-gray-900">Total Users</h3>
                <p className="mt-2 text-3xl font-bold text-purple-600">{stats.total_users || 0}</p>
              </Card>
              <Card>
                <h3 className="text-lg font-medium text-gray-900">Active Sessions</h3>
                <p className="mt-2 text-3xl font-bold text-orange-600">{stats.active_sessions || 0}</p>
              </Card>
              <Card>
                <h3 className="text-lg font-medium text-gray-900">API Calls Today</h3>
                <p className="mt-2 text-3xl font-bold text-indigo-600">{stats.api_calls_today || 0}</p>
              </Card>
              <Card>
                <h3 className="text-lg font-medium text-gray-900">Cache Hit Rate</h3>
                <p className="mt-2 text-3xl font-bold text-teal-600">
                  {stats.cache_hit_rate ? `${(stats.cache_hit_rate * 100).toFixed(1)}%` : 'N/A'}
                </p>
              </Card>
            </>
          )}
        </div>
      );
    }

    return null;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Open Data Explorer</h1>
        <p className="mt-2 text-gray-600">
          Browse and search public educational content and statistics.
        </p>
      </div>

      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('content')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'content'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Public Content
          </button>
          <button
            onClick={() => setActiveTab('events')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'events'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Events & Schedules
          </button>
          <button
            onClick={() => setActiveTab('stats')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'stats'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Statistics
          </button>
        </nav>
      </div>

      <div className="py-6">
        {renderContent()}
      </div>

      {activeTab === 'events' && (
        <Card className="bg-yellow-50 border-yellow-200">
          <div className="text-yellow-800">
            <h3 className="font-medium">Events & Schedules Coming Soon</h3>
            <p className="mt-1 text-sm">
              This feature is currently under development. Check back soon!
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}