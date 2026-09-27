const isLocalDevelopment = ['localhost', '127.0.0.1'].includes(
  window.location.hostname
);


export const API_ROOT = isLocalDevelopment
  ? 'http://localhost:8000'
  : `${window.location.origin}/api`;

const websocketProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

export const WEBSOCKET_ROOT = isLocalDevelopment
  ? `${websocketProtocol}//localhost:8000`
  : `${websocketProtocol}//${window.location.host}`;


export function apiEndpoint(path = ''): string {
  const normalizedPath = path.replace(/^\/+/, '');
  return normalizedPath ? `${API_ROOT}/${normalizedPath}` : API_ROOT;
}
