import {
  Injectable
} from '@angular/core';

import {
  HttpClient
} from '@angular/common/http';

import {
  Observable
} from 'rxjs';
import { PriceSnapshot } from './product.service';


export interface ShoppingListItem extends PriceSnapshot {
  id: number;

  product?: number | null;

  product_name?: string;

  name: string;

  quantity: number | null;

  unit: string;

  note: string;

  is_checked: boolean;

  created_at?: string;

  shopping_category?: string;

  shopping_category_label?: string;

  shopping_category_order?: number;
}


export interface ShoppingList {
  id: number;

  title: string;

  created_at: string;

  updated_at: string;

  item_count: number;

  completed_count: number;

  estimated_total?: number | null;

  items: ShoppingListItem[];
}


export interface CreateShoppingListItemPayload extends PriceSnapshot {
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
          false,

        estimated_price: item.estimated_price ?? null,
        price_source: item.price_source ?? '',
        price_currency: item.price_currency ?? 'EUR',
        price_date: item.price_date ?? null,
        price_store: item.price_store ?? '',
        price_sample_count: item.price_sample_count ?? 0,
        price_min: item.price_min ?? null,
        price_max: item.price_max ?? null,
        package_price: item.package_price ?? null,
        package_quantity: item.package_quantity ?? null,
        package_unit: item.package_unit ?? ''
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
