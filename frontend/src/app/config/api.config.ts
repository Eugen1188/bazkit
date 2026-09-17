const isLocalDevelopment = ['localhost', '127.0.0.1'].includes(
  window.location.hostname
);


export const API_ROOT = isLocalDevelopment
  ? 'http://localhost:8000'
  : `http://${window.location.hostname}:8000`;

const websocketProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

export const WEBSOCKET_ROOT = `${websocketProtocol}//${window.location.hostname}:8000`;


export function apiEndpoint(path = ''): string {
  const normalizedPath = path.replace(/^\/+/, '');
  return normalizedPath ? `${API_ROOT}/${normalizedPath}` : API_ROOT;
}
