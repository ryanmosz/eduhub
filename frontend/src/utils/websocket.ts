/**
 * WebSocket URL utility
 * Handles WebSocket URL construction for different environments
 */

export function getWebSocketUrl(path: string = '/alerts/ws'): string {
  const apiUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  
  // Parse the API URL to get the host
  let wsUrl: string;
  
  try {
    const url = new URL(apiUrl);
    
    // Determine WebSocket protocol based on HTTP protocol
    const wsProtocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    
    // Construct WebSocket URL
    wsUrl = `${wsProtocol}//${url.host}${path}`;
  } catch (error) {
    // Fallback for development
    console.warn('Failed to parse API URL, using fallback WebSocket URL');
    wsUrl = `ws://localhost:8000${path}`;
  }
  
  console.log('WebSocket URL:', wsUrl);
  return wsUrl;
}