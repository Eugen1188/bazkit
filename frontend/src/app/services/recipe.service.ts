import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
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

export interface GenerateRecipePayload {
  idea: string;
  available_ingredients: string;
  avoid_ingredients: string;
  diet: string;
  servings: number;
  max_time: number;
  category: string;
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
}

export interface RecipePayload {
  name: string;
  description: string;
  servings: number;
  preparation_time: number | null;
  category: string;
  instructions: string;
  notes: string;
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

  getRecipe(id: number): Observable<Recipe> {
    return this.http.get<Recipe>(`${this.apiUrl}${id}/`);
  }

  createRecipe(payload: RecipePayload): Observable<Recipe> {
    return this.http.post<Recipe>(this.apiUrl, payload);
  }

  updateRecipe(id: number, payload: RecipePayload): Observable<Recipe> {
    return this.http.put<Recipe>(`${this.apiUrl}${id}/`, payload);
  }

  deleteRecipe(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}${id}/`);
  }

  generateRecipe(payload: GenerateRecipePayload): Observable<GeneratedRecipe> {
    return this.http.post<GeneratedRecipe>(`${this.apiUrl}generate/`, payload);
  }
}
