import {
  Injectable
} from '@angular/core';

import {
  HttpClient
} from '@angular/common/http';

import {
  Observable
} from 'rxjs';


export interface RecipeIngredient {
  id?: number;

  name: string;

  quantity:
    number | null;

  unit: string;
}


export interface Recipe {
  id: number;

  name: string;

  description: string;

  servings: number;

  preparation_time:
    number | null;

  category: string;

  instructions: string;

  notes: string;

  created_at: string;

  updated_at: string;

  ingredients:
    RecipeIngredient[];
}


export interface RecipePayload {
  name: string;

  description: string;

  servings: number;

  preparation_time:
    number | null;

  category: string;

  instructions: string;

  notes: string;

  ingredients:
    RecipeIngredient[];
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

  ingredients:
    RecipeIngredient[];

  steps:
    string[];

  notes: string;
}


@Injectable({
  providedIn: 'root'
})
export class RecipeService {

  private apiUrl =
    'http://178.104.47.231:8000/recipes/';


  constructor(
    private http:
      HttpClient
  ) {}


  getRecipes():
    Observable<Recipe[]> {

    return this.http.get<Recipe[]>(
      this.apiUrl
    );
  }


  getRecipe(
    id: number
  ): Observable<Recipe> {

    return this.http.get<Recipe>(
      `${this.apiUrl}${id}/`
    );
  }


  createRecipe(
    payload: RecipePayload
  ): Observable<Recipe> {

    return this.http.post<Recipe>(
      this.apiUrl,
      payload
    );
  }


  updateRecipe(
    id: number,
    payload: RecipePayload
  ): Observable<Recipe> {

    return this.http.put<Recipe>(
      `${this.apiUrl}${id}/`,
      payload
    );
  }


  deleteRecipe(
    id: number
  ): Observable<void> {

    return this.http.delete<void>(
      `${this.apiUrl}${id}/`
    );
  }


  generateRecipe(
    payload:
      GenerateRecipePayload
  ): Observable<GeneratedRecipe> {

    return this.http.post<GeneratedRecipe>(
      `${this.apiUrl}generate/`,
      payload
    );
  }
}