import { useQuery } from '@tanstack/react-query';

interface CourseResource {
  id: string;
  title: string;
  description: string;
  type: string;
  url: string;
  embedUrl?: string;
  duration?: string;
  instructor?: string;
}

interface Course {
  id: string;
  title: string;
  description: string;
  department: string;
  instructor: string;
  students: number;
  status: string;
  resources: CourseResource[];
  progress?: number;
}

interface Announcement {
  id: string;
  title: string;
  content: string;
  type: 'info' | 'warning' | 'success';
  created: string;
  author?: string;
}

export function useCourses() {
  return useQuery<Course[]>({
    queryKey: ['courses'],
    queryFn: async () => {
      const response = await fetch('/api/courses/', {
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch courses');
      }
      
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // Refetch every 30 seconds to get updates from Plone
  });
}

export function useAnnouncements(limit: number = 5) {
  return useQuery<Announcement[]>({
    queryKey: ['announcements', limit],
    queryFn: async () => {
      const response = await fetch(`/api/courses/announcements?limit=${limit}`, {
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch announcements');
      }
      
      return response.json();
    },
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 60 * 1000, // Refetch every minute for fresh announcements
  });
}