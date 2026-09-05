import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {
  BehaviorSubject,
  Observable,
  finalize,
  of,
  shareReplay,
  tap,
} from 'rxjs';


export interface AIRecipeUsage {
  plan: 'free' | 'premium';
  plan_label: string;
  is_premium: boolean;
  premium_enforcement_enabled: boolean;
  used: number;
  limit: number;
  remaining: number;
  period_start: string;
  resets_at: string;
}


@Injectable({ providedIn: 'root' })
export class AIUsageService {
  private readonly apiUrl = `${this.getApiBaseUrl()}/recipes/ai-usage/`;
  private readonly usageSubject = new BehaviorSubject<AIRecipeUsage | null>(null);
  private activeRequest: Observable<AIRecipeUsage> | null = null;

  readonly usage$ = this.usageSubject.asObservable();

  constructor(private readonly http: HttpClient) {
    window.addEventListener('bazkit:logout', () => {
      this.usageSubject.next(null);
      this.activeRequest = null;
    });
  }

  get current(): AIRecipeUsage | null {
    return this.usageSubject.value;
  }

  load(forceRefresh = false): Observable<AIRecipeUsage> {
    if (!forceRefresh && this.current) return of(this.current);
    if (this.activeRequest) return this.activeRequest;

    this.activeRequest = this.http.get<AIRecipeUsage>(this.apiUrl).pipe(
      tap(usage => this.setUsage(usage)),
      finalize(() => { this.activeRequest = null; }),
      shareReplay({ bufferSize: 1, refCount: false }),
    );
    return this.activeRequest;
  }

  setUsage(usage: AIRecipeUsage): void {
    this.usageSubject.next(usage);
  }

  private getApiBaseUrl(): string {
    return window.location.hostname === 'localhost'
      || window.location.hostname === '127.0.0.1'
      ? 'http://localhost:8000'
      : 'http://178.104.47.231:8000';
  }
}
