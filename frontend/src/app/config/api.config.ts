const isLocalDevelopment = ['localhost', '127.0.0.1'].includes(
  window.location.hostname
);

declare global {
  interface Window {
    __BAZKIT_API_ROOT__?: string;
    __BAZKIT_WEBSOCKET_ROOT__?: string;
  }
}


export const API_ROOT = window.__BAZKIT_API_ROOT__ || (
  isLocalDevelopment
    ? 'http://localhost:8000'
    : `${window.location.origin}/api`
);

const websocketProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

export const WEBSOCKET_ROOT = window.__BAZKIT_WEBSOCKET_ROOT__ || (
  isLocalDevelopment
    ? `${websocketProtocol}//localhost:8000`
    : `${websocketProtocol}//${window.location.host}`
);


export function apiEndpoint(path = ''): string {
  const normalizedPath = path.replace(/^\/+/, '');
  return normalizedPath ? `${API_ROOT}/${normalizedPath}` : API_ROOT;
}
