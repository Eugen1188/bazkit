import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { finalize, Observable, of, shareReplay, tap } from 'rxjs';
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
  is_common_pantry?: boolean;
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


@Injectable({ providedIn: 'root' })
export class ShoppingListService {
  private static readonly cacheLifetimeMs = 60_000;

  private readonly apiUrl = 'http://178.104.47.231:8000/lists/shopping-list/';
  private cachedList: ShoppingList | null = null;
  private cacheExpiresAt = 0;
  private cacheSession = '';
  private inFlightRequest: Observable<ShoppingList> | null = null;


  constructor(private readonly http: HttpClient) {}


  private currentSession(): string {
    return localStorage.getItem('access_token') ?? '';
  }


  private ensureSession(): string {
    const session = this.currentSession();

    if (session !== this.cacheSession) {
      this.cacheSession = session;
      this.cachedList = null;
      this.cacheExpiresAt = 0;
      this.inFlightRequest = null;
    }

    return session;
  }


  private remember(list: ShoppingList, session = this.currentSession()): void {
    if (session !== this.currentSession()) return;

    this.cacheSession = session;
    this.cachedList = list;
    this.cacheExpiresAt = Date.now() + ShoppingListService.cacheLifetimeMs;
  }


  private updateCachedItems(
    update: (items: ShoppingListItem[]) => ShoppingListItem[],
    session: string
  ): void {
    this.ensureSession();
    if (session !== this.currentSession() || !this.cachedList) return;

    const items = update(this.cachedList.items ?? []);
    this.remember({
      ...this.cachedList,
      items,
      item_count: items.length,
      completed_count: items.filter(item => item.is_checked).length
    });
  }


  getShoppingList(forceRefresh = false): Observable<ShoppingList> {
    const session = this.ensureSession();

    if (
      !forceRefresh &&
      this.cachedList &&
      Date.now() < this.cacheExpiresAt
    ) {
      return of(this.cachedList);
    }

    if (!forceRefresh && this.inFlightRequest) {
      return this.inFlightRequest;
    }

    const request = this.http.get<ShoppingList>(this.apiUrl).pipe(
      tap(list => this.remember(list, session)),
      finalize(() => {
        if (this.inFlightRequest === request) {
          this.inFlightRequest = null;
        }
      }),
      shareReplay({ bufferSize: 1, refCount: false })
    );

    this.inFlightRequest = request;
    return request;
  }


  addItem(item: CreateShoppingListItemPayload): Observable<ShoppingListItem> {
    const session = this.ensureSession();
    return this.http.post<ShoppingListItem>(`${this.apiUrl}items/`, {
      product: item.product ?? null,
      name: item.name,
      quantity: item.quantity,
      unit: item.unit,
      note: item.note ?? '',
      is_checked: false,
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
    }).pipe(
      tap(createdItem => this.updateCachedItems(
        items => (
          items.some(existing => existing.id === createdItem.id)
            ? items
            : [...items, createdItem]
        ),
        session
      ))
    );
  }


  addSavedList(savedListId: number): Observable<ShoppingList> {
    const session = this.ensureSession();
    return this.http.post<ShoppingList>(
      `${this.apiUrl}add-saved-list/${savedListId}/`,
      {}
    ).pipe(tap(list => this.remember(list, session)));
  }


  addRecipe(
    recipeId: number,
    includedPantryProductIds?: number[]
  ): Observable<ShoppingList> {
    const session = this.ensureSession();
    return this.http.post<ShoppingList>(
      `${this.apiUrl}add-recipe/${recipeId}/`,
      includedPantryProductIds === undefined
        ? {}
        : { included_pantry_product_ids: includedPantryProductIds }
    ).pipe(tap(list => this.remember(list, session)));
  }


  updateItem(
    itemId: number,
    data: Partial<ShoppingListItem>
  ): Observable<ShoppingListItem> {
    const session = this.ensureSession();
    return this.http.patch<ShoppingListItem>(
      `${this.apiUrl}items/${itemId}/`,
      data
    ).pipe(
      tap(updatedItem => this.updateCachedItems(
        items => items.map(item => (
          item.id === updatedItem.id ? updatedItem : item
        )),
        session
      ))
    );
  }


  deleteItem(itemId: number): Observable<void> {
    const session = this.ensureSession();
    return this.http.delete<void>(`${this.apiUrl}items/${itemId}/`).pipe(
      tap(() => this.updateCachedItems(
        items => items.filter(item => item.id !== itemId),
        session
      ))
    );
  }


  clearShoppingList(): Observable<ShoppingList> {
    const session = this.ensureSession();
    return this.http.delete<ShoppingList>(this.apiUrl).pipe(
      tap(list => this.remember(list, session))
    );
  }
}
