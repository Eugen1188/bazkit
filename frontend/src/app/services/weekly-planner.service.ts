import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, shareReplay, tap } from 'rxjs';

import { RecipeNumberValue } from './recipe.service';
import { ShoppingList } from './shopping-list.service';


export type PlannerMealType = 'breakfast' | 'lunch' | 'dinner';

export interface PlannerRecipeSummary {
  id: number;
  name: string;
  image_url: string | null;
  image_position_x?: number;
  image_position_y?: number;
  image_zoom?: number;
  category: string;
  servings: number;
  calories: RecipeNumberValue;
  protein: RecipeNumberValue;
  carbohydrates: RecipeNumberValue;
  fat: RecipeNumberValue;
  fiber: RecipeNumberValue;
  estimated_price: RecipeNumberValue;
  ingredient_count: number;
}

export interface WeeklyPlanEntry {
  id: number;
  date: string;
  meal_type: PlannerMealType;
  servings: number;
  recipe: number;
  recipe_detail: PlannerRecipeSummary;
  created_at: string;
  updated_at: string;
}

export interface WeeklyPlanEntryPayload {
  date: string;
  meal_type: PlannerMealType;
  servings: number;
  recipe: number;
}

export interface GeneratedWeekResponse {
  entries: WeeklyPlanEntry[];
  changed_count: number;
  planning_method: 'ai' | 'automatic';
  message: string;
}

export interface WeeklyPlanGenerationOptions {
  meal_types: PlannerMealType[];
  daily_calorie_target: number | null;
  daily_protein_target: number | null;
  max_recipe_repeats: number;
  servings: number;
  overwrite: boolean;
}

export interface WeeklyShoppingListResponse {
  shopping_list: ShoppingList;
  meal_count: number;
  ingredient_count: number;
  product_count: number;
  message: string;
}


@Injectable({ providedIn: 'root' })
export class WeeklyPlannerService {
  private readonly apiUrl = this.getApiUrl();
  private readonly cacheLifetimeMs = 60_000;
  private cacheSession = '';
  private readonly entryCache = new Map<
    string,
    { expiresAt: number; request: Observable<WeeklyPlanEntry[]> }
  >();

  constructor(private readonly http: HttpClient) {}

  private getApiUrl(): string {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000/planner/';
    }
    return 'http://178.104.47.231:8000/planner/';
  }

  getEntries(start: string, end: string): Observable<WeeklyPlanEntry[]> {
    const session = localStorage.getItem('access_token') ?? '';
    if (session !== this.cacheSession) {
      this.cacheSession = session;
      this.entryCache.clear();
    }

    const cacheKey = `${start}:${end}`;
    const cached = this.entryCache.get(cacheKey);
    if (cached && Date.now() < cached.expiresAt) return cached.request;

    const params = new HttpParams().set('start', start).set('end', end);
    const request = this.http.get<WeeklyPlanEntry[]>(
      `${this.apiUrl}entries/`,
      { params }
    ).pipe(shareReplay({ bufferSize: 1, refCount: false }));
    this.entryCache.set(cacheKey, {
      request,
      expiresAt: Date.now() + this.cacheLifetimeMs
    });
    return request;
  }

  saveEntry(payload: WeeklyPlanEntryPayload): Observable<WeeklyPlanEntry> {
    return this.http.post<WeeklyPlanEntry>(`${this.apiUrl}entries/`, payload).pipe(
      tap(() => this.entryCache.clear())
    );
  }

  updateEntry(entryId: number, payload: WeeklyPlanEntryPayload): Observable<WeeklyPlanEntry> {
    return this.http.patch<WeeklyPlanEntry>(`${this.apiUrl}entries/${entryId}/`, payload).pipe(
      tap(() => this.entryCache.clear())
    );
  }

  deleteEntry(entryId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}entries/${entryId}/`).pipe(
      tap(() => this.entryCache.clear())
    );
  }

  generateWeek(
    start: string,
    end: string,
    options: WeeklyPlanGenerationOptions
  ): Observable<GeneratedWeekResponse> {
    return this.http.post<GeneratedWeekResponse>(`${this.apiUrl}generate/`, {
      start,
      end,
      ...options
    }).pipe(tap(() => this.entryCache.clear()));
  }

  createShoppingList(
    start: string,
    end: string,
    includedPantryProductIds?: number[]
  ): Observable<WeeklyShoppingListResponse> {
    return this.http.post<WeeklyShoppingListResponse>(`${this.apiUrl}shopping-list/`, {
      start,
      end,
      ...(includedPantryProductIds === undefined
        ? {}
        : { included_pantry_product_ids: includedPantryProductIds })
    });
  }
}
