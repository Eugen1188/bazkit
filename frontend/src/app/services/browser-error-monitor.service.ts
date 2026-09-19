import { ErrorHandler, Injectable } from '@angular/core';

import { apiEndpoint } from '../config/api.config';


interface BrowserIssue {
  message: string;
  type: string;
  stack: string;
  path: string;
}


@Injectable({ providedIn: 'root' })
export class BrowserErrorMonitorService {
  private readonly endpoint = apiEndpoint('monitoring/browser-errors/');
  private readonly recentlyReported = new Map<string, number>();
  private started = false;

  start(): void {
    if (this.started || typeof window === 'undefined') return;
    this.started = true;

    window.addEventListener('error', event => {
      this.report(event.error ?? event.message, {
        type: event.error?.name ?? 'WindowError',
        stack: event.error?.stack ?? `${event.filename}:${event.lineno}:${event.colno}`,
      });
    });
    window.addEventListener('unhandledrejection', event => {
      this.report(event.reason, { type: 'UnhandledPromiseRejection' });
    });
  }

  report(error: unknown, overrides: Partial<BrowserIssue> = {}): void {
    const normalized = this.normalize(error, overrides);
    const fingerprint = `${normalized.type}|${normalized.message}|${normalized.path}`;
    const now = Date.now();
    const previous = this.recentlyReported.get(fingerprint) ?? 0;
    if (now - previous < 60_000) return;
    this.recentlyReported.set(fingerprint, now);

    if (this.recentlyReported.size > 100) {
      for (const [key, timestamp] of this.recentlyReported) {
        if (now - timestamp >= 60_000) this.recentlyReported.delete(key);
      }
    }

    void window.fetch(this.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(normalized),
      keepalive: true,
      credentials: 'omit',
    }).catch(() => undefined);
  }

  private normalize(error: unknown, overrides: Partial<BrowserIssue>): BrowserIssue {
    const nativeError = error instanceof Error ? error : null;
    const message = nativeError?.message ?? String(error ?? 'Unbekannter Browserfehler');
    return {
      message: (overrides.message ?? message).slice(0, 500),
      type: (overrides.type ?? nativeError?.name ?? 'BrowserError').slice(0, 100),
      stack: (overrides.stack ?? nativeError?.stack ?? '').slice(0, 4000),
      path: (overrides.path ?? `${window.location.pathname}${window.location.search}`).slice(0, 500),
    };
  }
}


@Injectable()
export class BazkitErrorHandler implements ErrorHandler {
  constructor(private readonly monitor: BrowserErrorMonitorService) {}

  handleError(error: unknown): void {
    this.monitor.report(error);
    console.error(error);
  }
}


export function startBrowserErrorMonitoring(
  monitor: BrowserErrorMonitorService,
): () => void {
  return () => monitor.start();
}
