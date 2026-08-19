import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface SavedListItem {
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

  items?: SavedListItem[];
}

export interface CreateSavedListPayload {
  title: string;

  items: SavedListItem[];
}

@Injectable({
  providedIn: 'root',
})
export class SavedListService {

  private apiUrl =
    'http://178.104.47.231:8000/lists/saved-lists/';


  constructor(
    private http: HttpClient
  ) {}


  createSavedList(
    payload: CreateSavedListPayload
  ): Observable<SavedList> {

    return this.http.post<SavedList>(
      this.apiUrl,
      payload
    );
  }


  getSavedLists():
    Observable<SavedList[]> {

    return this.http.get<SavedList[]>(
      this.apiUrl
    );
  }


  getSavedList(
    id: number
  ): Observable<SavedList> {

    return this.http.get<SavedList>(
      `${this.apiUrl}${id}/`
    );
  }


  updateSavedList(
    id: number,
    payload: CreateSavedListPayload
  ): Observable<SavedList> {

    return this.http.put<SavedList>(
      `${this.apiUrl}${id}/`,
      payload
    );
  }


  deleteSavedList(
    id: number
  ): Observable<void> {

    return this.http.delete<void>(
      `${this.apiUrl}${id}/`
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
        name: item.name,
        quantity: item.quantity,
        unit: item.unit,
        note: item.note ?? ''
      }
    );
  }


  deleteSavedListItem(
    listId: number,
    itemId: number
  ): Observable<void> {

    return this.http.delete<void>(
      `${this.apiUrl}${listId}/items/${itemId}/`
    );
  }
}