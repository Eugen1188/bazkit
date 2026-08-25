import {
  Injectable
} from '@angular/core';

import {
  HttpClient
} from '@angular/common/http';

import {
  Observable
} from 'rxjs';


export interface ShoppingListItem {
  id: number;

  product?: number | null;

  product_name?: string;

  name: string;

  quantity: number | null;

  unit: string;

  note: string;

  is_checked: boolean;

  created_at?: string;
}


export interface ShoppingList {
  id: number;

  title: string;

  created_at: string;

  updated_at: string;

  item_count: number;

  completed_count: number;

  items: ShoppingListItem[];
}


export interface CreateShoppingListItemPayload {
  product?: number | null;

  name: string;

  quantity: number;

  unit: string;

  note?: string;
}


@Injectable({
  providedIn: 'root'
})
export class ShoppingListService {

  private apiUrl =
    'http://178.104.47.231:8000/lists/shopping-list/';


  constructor(
    private http: HttpClient
  ) {}


  getShoppingList():
    Observable<ShoppingList> {

    return this.http.get<ShoppingList>(
      this.apiUrl
    );
  }


  addItem(
    item: CreateShoppingListItemPayload
  ): Observable<ShoppingListItem> {

    return this.http.post<ShoppingListItem>(
      `${this.apiUrl}items/`,
      {
        product:
          item.product ?? null,

        name:
          item.name,

        quantity:
          item.quantity,

        unit:
          item.unit,

        note:
          item.note ?? '',

        is_checked:
          false
      }
    );
  }


  addSavedList(
    savedListId: number
  ): Observable<ShoppingList> {

    return this.http.post<ShoppingList>(
      `${this.apiUrl}add-saved-list/${savedListId}/`,
      {}
    );
  }


  addRecipe(
    recipeId: number
  ): Observable<ShoppingList> {

    return this.http.post<ShoppingList>(
      `${this.apiUrl}add-recipe/${recipeId}/`,
      {}
    );
  }


  updateItem(
    itemId: number,
    data: Partial<ShoppingListItem>
  ): Observable<ShoppingListItem> {

    return this.http.patch<ShoppingListItem>(
      `${this.apiUrl}items/${itemId}/`,
      data
    );
  }


  deleteItem(
    itemId: number
  ): Observable<void> {

    return this.http.delete<void>(
      `${this.apiUrl}items/${itemId}/`
    );
  }


  clearShoppingList():
    Observable<ShoppingList> {

    return this.http.delete<ShoppingList>(
      this.apiUrl
    );
  }
}
