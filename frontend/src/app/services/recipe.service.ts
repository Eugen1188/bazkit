import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of, shareReplay, tap } from 'rxjs';
import { PriceSnapshot, ProductSuggestion } from './product.service';

export interface RecipeIngredient extends PriceSnapshot {
  id?: number;
  product?: number | null;
  product_detail?: ProductSuggestion | null;
  name: string;
  quantity: number | null;
  unit: string;
}

export type RecipeNumberValue = number | string | null;

export interface Recipe {
  id: number;
  image_url: string | null;
  image_position_x?: number;
  image_position_y?: number;
  image_zoom?: number;
  name: string;
  description: string;
  servings: number;
  preparation_time: number | null;
  category: string;
  instructions: string;
  notes: string;
  calories: RecipeNumberValue;
  protein: RecipeNumberValue;
  carbohydrates: RecipeNumberValue;
  fat: RecipeNumberValue;
  fiber: RecipeNumberValue;
  estimated_price: RecipeNumberValue;
  estimated_price_per_serving: RecipeNumberValue;
  price_ingredient_count: number;
  price_missing_ingredient_count: number;
  price_coverage_percent: number;
  price_is_complete: boolean;
  price_is_sufficient: boolean;
  created_at: string;
  updated_at: string;
  ingredients: RecipeIngredient[];
}

export interface RecipeSummary {
  id: number;
  image_url: string | null;
  image_position_x?: number;
  image_position_y?: number;
  image_zoom?: number;
  name: string;
  description: string;
  servings: number;
  preparation_time: number | null;
  category: string;
  calories: RecipeNumberValue;
  protein: RecipeNumberValue;
  carbohydrates: RecipeNumberValue;
  fat: RecipeNumberValue;
  fiber: RecipeNumberValue;
  estimated_price: RecipeNumberValue;
  ingredient_count: number;
  created_at: string;
  updated_at: string;
  ingredients?: RecipeIngredient[];
}

export interface GenerateRecipePayload {
  idea: string;
  available_ingredients: string;
  avoid_ingredients: string;
  diet: string;
  servings: number;
  max_time: number;
  category: string;
  dietary_preferences: string[];
  favorite_cuisines: string[];
}

export interface GeneratedRecipe {
  name: string;
  description: string;
  servings: number;
  preparation_time: number;
  category: string;
  ingredients: RecipeIngredient[];
  steps: string[];
  notes: string;
  nutrition: {
    calories: number;
    protein: number;
    carbohydrates: number;
    fat: number;
    fiber: number;
  };
  nutrition_complete: boolean;
  nutrition_source: string;
}

export interface RecipePayload {
  name: string;
  description: string;
  servings: number;
  preparation_time: number | null;
  category: string;
  instructions: string;
  notes: string;
  image_position_x: number;
  image_position_y: number;
  image_zoom: number;
  calories?: number | null;
  protein?: number | null;
  carbohydrates?: number | null;
  fat?: number | null;
  fiber?: number | null;
  estimated_price?: number | null;
  ingredients: RecipeIngredient[];
}

@Injectable({ providedIn: 'root' })
export class RecipeService {
  private readonly apiUrl = this.getApiUrl();
  private readonly summaryCacheLifetimeMs = 60_000;
  private summaryCacheSession = '';
  private summaryCacheExpiresAt = 0;
  private summaryRequest: Observable<RecipeSummary[]> | null = null;

  constructor(private readonly http: HttpClient) {}

  private getApiUrl(): string {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000/recipes/';
    }
    return 'http://178.104.47.231:8000/recipes/';
  }

  getRecipes(): Observable<Recipe[]> {
    return this.http.get<Recipe[]>(this.apiUrl);
  }

  getRecipeSummaries(forceRefresh = false): Observable<RecipeSummary[]> {
    const session = localStorage.getItem('access_token') ?? '';

    if (session !== this.summaryCacheSession) {
      this.summaryCacheSession = session;
      this.summaryCacheExpiresAt = 0;
      this.summaryRequest = null;
    }

    if (
      !forceRefresh &&
      this.summaryRequest &&
      Date.now() < this.summaryCacheExpiresAt
    ) {
      return this.summaryRequest;
    }

    const params = new HttpParams().set('summary', '1');
    this.summaryCacheExpiresAt = Date.now() + this.summaryCacheLifetimeMs;
    this.summaryRequest = this.http.get<RecipeSummary[]>(this.apiUrl, { params }).pipe(
      shareReplay({ bufferSize: 1, refCount: false })
    );
    return this.summaryRequest;
  }

  private invalidateSummaryCache(): void {
    this.summaryCacheExpiresAt = 0;
    this.summaryRequest = null;
  }

  getRecipesByIds(ids: number[]): Observable<Recipe[]> {
    const uniqueIds = Array.from(new Set(ids.filter(id => Number.isInteger(id) && id > 0)));
    if (!uniqueIds.length) return of([]);
    const params = new HttpParams().set('ids', uniqueIds.join(','));
    return this.http.get<Recipe[]>(this.apiUrl, { params });
  }

  getRecipe(id: number): Observable<Recipe> {
    return this.http.get<Recipe>(`${this.apiUrl}${id}/`);
  }

  createRecipe(payload: RecipePayload): Observable<Recipe> {
    return this.http.post<Recipe>(this.apiUrl, payload).pipe(
      tap(() => this.invalidateSummaryCache())
    );
  }

  updateRecipe(id: number, payload: RecipePayload): Observable<Recipe> {
    return this.http.put<Recipe>(`${this.apiUrl}${id}/`, payload).pipe(
      tap(() => this.invalidateSummaryCache())
    );
  }

  uploadRecipeImage(id: number, image: File): Observable<Recipe> {
    const formData = new FormData();
    formData.append('image', image, image.name);
    return this.http.post<Recipe>(`${this.apiUrl}${id}/image/`, formData).pipe(
      tap(() => this.invalidateSummaryCache())
    );
  }

  deleteRecipeImage(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}${id}/image/`).pipe(
      tap(() => this.invalidateSummaryCache())
    );
  }

  deleteRecipe(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}${id}/`).pipe(
      tap(() => this.invalidateSummaryCache())
    );
  }

  generateRecipe(payload: GenerateRecipePayload): Observable<GeneratedRecipe> {
    return this.http.post<GeneratedRecipe>(`${this.apiUrl}generate/`, payload);
  }
}
