import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, shareReplay, tap } from 'rxjs';
import { PriceSnapshot } from './product.service';


export interface SavedListItem extends PriceSnapshot {
  id?: number;
  product?: number | null;
  product_name?: string;
  name: string;
  quantity: number;
  unit: string;
  note?: string;
}


export interface SavedList {
  id: number;
  title: string;
  created_at: string;
  item_count: number;
  estimated_total?: number | null;
  items?: SavedListItem[];
}


export interface CreateSavedListPayload {
  title: string;
  items: SavedListItem[];
}


@Injectable({ providedIn: 'root' })
export class SavedListService {
  private readonly apiUrl = 'http://178.104.47.231:8000/lists/saved-lists/';
  private readonly cacheLifetimeMs = 60_000;
  private cacheSession = '';
  private cacheExpiresAt = 0;
  private listRequest: Observable<SavedList[]> | null = null;


  constructor(private readonly http: HttpClient) {}


  private invalidateListCache(): void {
    this.cacheExpiresAt = 0;
    this.listRequest = null;
  }


  createSavedList(payload: CreateSavedListPayload): Observable<SavedList> {
    return this.http.post<SavedList>(this.apiUrl, payload).pipe(
      tap(() => this.invalidateListCache())
    );
  }


  getSavedLists(forceRefresh = false): Observable<SavedList[]> {
    const session = localStorage.getItem('access_token') ?? '';
    if (session !== this.cacheSession) {
      this.cacheSession = session;
      this.invalidateListCache();
    }

    if (
      !forceRefresh &&
      this.listRequest &&
      Date.now() < this.cacheExpiresAt
    ) {
      return this.listRequest;
    }

    this.cacheExpiresAt = Date.now() + this.cacheLifetimeMs;
    this.listRequest = this.http.get<SavedList[]>(this.apiUrl).pipe(
      shareReplay({ bufferSize: 1, refCount: false })
    );
    return this.listRequest;
  }


  getSavedList(id: number): Observable<SavedList> {
    return this.http.get<SavedList>(`${this.apiUrl}${id}/`);
  }


  updateSavedList(
    id: number,
    payload: CreateSavedListPayload
  ): Observable<SavedList> {
    return this.http.put<SavedList>(`${this.apiUrl}${id}/`, payload).pipe(
      tap(() => this.invalidateListCache())
    );
  }


  deleteSavedList(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}${id}/`).pipe(
      tap(() => this.invalidateListCache())
    );
  }


  updateSavedListItem(
    listId: number,
    itemId: number,
    item: SavedListItem
  ): Observable<SavedListItem> {
    return this.http.put<SavedListItem>(
      `${this.apiUrl}${listId}/items/${itemId}/`,
      {
        product: item.product ?? null,
        name: item.name,
        quantity: item.quantity,
        unit: item.unit,
        note: item.note ?? '',
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
    ).pipe(tap(() => this.invalidateListCache()));
  }


  deleteSavedListItem(listId: number, itemId: number): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}${listId}/items/${itemId}/`
    ).pipe(tap(() => this.invalidateListCache()));
  }
}
