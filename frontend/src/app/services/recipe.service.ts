import { Injectable } from '@angular/core';

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


@Injectable({
  providedIn: 'root'
})
export class RecipeService {

  private apiUrl =
    'http://178.104.47.231:8000/recipes/';


  constructor(
    private http: HttpClient
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
}