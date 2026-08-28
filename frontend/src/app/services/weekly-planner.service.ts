import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { RecipeNumberValue } from './recipe.service';
import { ShoppingList } from './shopping-list.service';


export type PlannerMealType = 'breakfast' | 'lunch' | 'dinner';

export interface PlannerRecipeSummary {
  id: number;
  name: string;
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

  constructor(private readonly http: HttpClient) {}

  private getApiUrl(): string {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000/planner/';
    }
    return 'http://178.104.47.231:8000/planner/';
  }

  getEntries(start: string, end: string): Observable<WeeklyPlanEntry[]> {
    const params = new HttpParams().set('start', start).set('end', end);
    return this.http.get<WeeklyPlanEntry[]>(`${this.apiUrl}entries/`, { params });
  }

  saveEntry(payload: WeeklyPlanEntryPayload): Observable<WeeklyPlanEntry> {
    return this.http.post<WeeklyPlanEntry>(`${this.apiUrl}entries/`, payload);
  }

  updateEntry(entryId: number, payload: WeeklyPlanEntryPayload): Observable<WeeklyPlanEntry> {
    return this.http.patch<WeeklyPlanEntry>(`${this.apiUrl}entries/${entryId}/`, payload);
  }

  deleteEntry(entryId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}entries/${entryId}/`);
  }

  generateWeek(start: string, end: string): Observable<GeneratedWeekResponse> {
    return this.http.post<GeneratedWeekResponse>(`${this.apiUrl}generate/`, {
      start,
      end,
      overwrite: false
    });
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
