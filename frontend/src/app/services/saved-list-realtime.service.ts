import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, Subscription } from 'rxjs';

import { WEBSOCKET_ROOT, apiEndpoint } from '../config/api.config';


export interface SavedListRealtimeEvent {
  type: 'connected' | 'disconnected' | 'saved-list.changed';
  list_id: number;
  action?: string;
  actor_id?: number | null;
  actor_name?: string;
}


@Injectable({ providedIn: 'root' })
export class SavedListRealtimeService {
  constructor(private readonly http: HttpClient) {}

  events(listId: number): Observable<SavedListRealtimeEvent> {
    return new Observable(observer => {
      let active = true;
      let socket: WebSocket | null = null;
      let ticketRequest: Subscription | null = null;
      let retryTimer: number | null = null;
      let retryDelay = 1000;

      const scheduleReconnect = (): void => {
        if (!active || !navigator.onLine || retryTimer !== null) return;
        retryTimer = window.setTimeout(() => {
          retryTimer = null;
          connect();
        }, retryDelay);
        retryDelay = Math.min(retryDelay * 2, 15_000);
      };

      const connect = (): void => {
        if (!active || !navigator.onLine || socket?.readyState === WebSocket.OPEN) return;
        ticketRequest?.unsubscribe();
        ticketRequest = this.http.post<{ ticket: string }>(
          apiEndpoint(`lists/saved-lists/${listId}/realtime-ticket/`),
          {}
        ).subscribe({
          next: response => {
            if (!active) return;
            socket = new WebSocket(
              `${WEBSOCKET_ROOT}/ws/saved-lists/${listId}/?ticket=${encodeURIComponent(response.ticket)}`
            );
            socket.onopen = () => { retryDelay = 1000; };
            socket.onmessage = message => {
              try {
                observer.next(JSON.parse(message.data) as SavedListRealtimeEvent);
              } catch {
                // Ignore malformed messages and keep the live connection open.
              }
            };
            socket.onerror = () => socket?.close();
            socket.onclose = () => {
              socket = null;
              if (active) {
                observer.next({ type: 'disconnected', list_id: listId });
                scheduleReconnect();
              }
            };
          },
          error: () => {
            observer.next({ type: 'disconnected', list_id: listId });
            scheduleReconnect();
          }
        });
      };

      const handleOnline = (): void => {
        retryDelay = 1000;
        connect();
      };
      const handleOffline = (): void => socket?.close();

      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);
      connect();

      return () => {
        active = false;
        ticketRequest?.unsubscribe();
        if (retryTimer !== null) window.clearTimeout(retryTimer);
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
        socket?.close();
      };
    });
  }
}
