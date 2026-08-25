import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface RecipeIngredient {
  product: number | null;
  name: string;
  quantity: number | null;
  unit: string;
}

export interface RecipePayload {
  name: string;
  description: string;
  servings: number;
  preparation_time: number | null;
  category: string;
  instructions: string;
  notes: string;
  calories: number | null;
  protein: number | null;
  carbohydrates: number | null;
  fat: number | null;
  fiber: number | null;
  estimated_price: number | null;
  ingredients: RecipeIngredient[];
}

@Injectable({ providedIn: 'root' })
export class RecipeService {
  private readonly apiUrl = '/api/recipes/';

  constructor(private readonly http: HttpClient) {}

  createRecipe(payload: RecipePayload): Observable<unknown> {
    return this.http.post(this.apiUrl, payload);
  }

  updateRecipe(id: number, payload: RecipePayload): Observable<unknown> {
    return this.http.put(`${this.apiUrl}${id}/`, payload);
  }
}
