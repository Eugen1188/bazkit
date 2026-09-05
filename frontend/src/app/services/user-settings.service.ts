import { DOCUMENT } from '@angular/common';
import { Inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';


export type ShoppingSorting = 'category' | 'alphabetical' | 'created';
export type AppearanceMode = 'light' | 'dark' | 'system';
export type AccentColor = 'green' | 'blue' | 'orange' | 'red';


export interface UserSettings {
  shopping_default_sorting: ShoppingSorting;
  shopping_default_unit: string;
  shopping_move_completed_to_bottom: boolean;
  recipe_default_portions: number;
  dietary_preferences: string[];
  favorite_cuisines: string[];
  appearance: AppearanceMode;
  accent_color: AccentColor;
  notification_shopping_reminders: boolean;
  notification_shared_lists: boolean;
  notification_product_updates: boolean;
  readonly premium_active?: boolean;
  updated_at?: string;
}


export const DEFAULT_USER_SETTINGS: UserSettings = {
  shopping_default_sorting: 'category',
  shopping_default_unit: 'Stück',
  shopping_move_completed_to_bottom: true,
  recipe_default_portions: 2,
  dietary_preferences: [],
  favorite_cuisines: [],
  appearance: 'system',
  accent_color: 'green',
  notification_shopping_reminders: true,
  notification_shared_lists: true,
  notification_product_updates: false,
};


interface AccentPalette {
  primary: string;
  hover: string;
  soft: string;
  softBackground: string;
  ring: string;
  focus: string;
}


@Injectable({ providedIn: 'root' })
export class UserSettingsService {
  private readonly apiUrl = `${this.getApiBaseUrl()}/users/me/settings/`;
  private readonly cacheKey = 'bazkit_user_settings';
  private readonly systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
  private readonly settingsSubject = new BehaviorSubject<UserSettings>(
    this.readCachedSettings()
  );

  readonly settings$ = this.settingsSubject.asObservable();

  private readonly accentPalettes: Record<AccentColor, AccentPalette> = {
    green: {
      primary: '#587664',
      hover: '#4f6a59',
      soft: '#8ba395',
      softBackground: '#eef4f0',
      ring: 'rgba(88, 118, 100, 0.16)',
      focus: '#476b57',
    },
    blue: {
      primary: '#4f7197',
      hover: '#456486',
      soft: '#8da7c1',
      softBackground: '#edf3f8',
      ring: 'rgba(79, 113, 151, 0.16)',
      focus: '#3e648c',
    },
    orange: {
      primary: '#a9672f',
      hover: '#955b2a',
      soft: '#c99c75',
      softBackground: '#faf1e9',
      ring: 'rgba(169, 103, 47, 0.17)',
      focus: '#8d5426',
    },
    red: {
      primary: '#a95656',
      hover: '#964a4a',
      soft: '#c58c8c',
      softBackground: '#f9eeee',
      ring: 'rgba(169, 86, 86, 0.16)',
      focus: '#8e4545',
    },
  };

  constructor(
    private readonly http: HttpClient,
    @Inject(DOCUMENT) private readonly document: Document,
  ) {
    this.applyToDocument(this.settingsSubject.value);
    window.addEventListener('bazkit:logout', () => this.clearCache());
    this.systemTheme.addEventListener('change', () => {
      if (this.current.appearance === 'system') {
        this.applyToDocument(this.current);
      }
    });
  }

  get current(): UserSettings {
    return this.settingsSubject.value;
  }

  load(): Observable<UserSettings> {
    return this.http.get<UserSettings>(this.apiUrl).pipe(
      tap(settings => this.acceptSettings(settings))
    );
  }

  save(settings: UserSettings): Observable<UserSettings> {
    return this.http.patch<UserSettings>(this.apiUrl, settings).pipe(
      tap(savedSettings => this.acceptSettings(savedSettings))
    );
  }

  preview(settings: UserSettings): void {
    this.settingsSubject.next(this.normalizeSettings(settings));
    this.applyToDocument(settings);
  }

  clearCache(): void {
    localStorage.removeItem(this.cacheKey);
    this.settingsSubject.next({ ...DEFAULT_USER_SETTINGS });
    this.applyToDocument(DEFAULT_USER_SETTINGS);
  }

  private acceptSettings(settings: UserSettings): void {
    const normalized = this.normalizeSettings(settings);
    localStorage.setItem(this.cacheKey, JSON.stringify(normalized));
    this.settingsSubject.next(normalized);
    this.applyToDocument(normalized);
  }

  private readCachedSettings(): UserSettings {
    try {
      const cached = localStorage.getItem(this.cacheKey);
      return cached
        ? this.normalizeSettings(JSON.parse(cached) as Partial<UserSettings>)
        : { ...DEFAULT_USER_SETTINGS };
    } catch {
      return { ...DEFAULT_USER_SETTINGS };
    }
  }

  private normalizeSettings(settings: Partial<UserSettings>): UserSettings {
    return {
      ...DEFAULT_USER_SETTINGS,
      ...settings,
      dietary_preferences: [...(settings.dietary_preferences ?? [])],
      favorite_cuisines: [...(settings.favorite_cuisines ?? [])],
    };
  }

  private applyToDocument(settings: UserSettings): void {
    const root = this.document.documentElement;
    const useDarkTheme = settings.appearance === 'dark'
      || (settings.appearance === 'system' && this.systemTheme.matches);
    root.dataset['theme'] = useDarkTheme ? 'dark' : 'light';
    root.dataset['accent'] = settings.accent_color;

    const palette = this.accentPalettes[settings.accent_color]
      ?? this.accentPalettes.green;
    root.style.setProperty('--color-primary', palette.primary);
    root.style.setProperty('--color-primary-hover', palette.hover);
    root.style.setProperty('--color-primary-soft', palette.soft);
    root.style.setProperty('--color-primary-soft-bg', palette.softBackground);
    root.style.setProperty('--color-primary-ring', palette.ring);
    root.style.setProperty('--color-focus', palette.focus);
  }

  private getApiBaseUrl(): string {
    return window.location.hostname === 'localhost'
      || window.location.hostname === '127.0.0.1'
      ? 'http://localhost:8000'
      : 'http://178.104.47.231:8000';
  }
}
