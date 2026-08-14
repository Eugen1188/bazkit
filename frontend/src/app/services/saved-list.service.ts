import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface SavedListItem {
  id?: number;
  product?: number | null;
  product_name?: string;
  name: string;
  quantity: number;
  unit: string;
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

  private apiUrl = 'http://178.104.47.231:8000/lists/saved-lists/';

  constructor(private http: HttpClient) {}

  createSavedList(
    payload: CreateSavedListPayload
  ): Observable<SavedList> {
    return this.http.post<SavedList>(
      this.apiUrl,
      payload,
      {
        headers: this.getHeaders()
      }
    );
  }

  getSavedLists(): Observable<SavedList[]> {
    return this.http.get<SavedList[]>(
      this.apiUrl,
      {
        headers: this.getHeaders()
      }
    );
  }

  getSavedList(id: number): Observable<SavedList> {
    return this.http.get<SavedList>(
      `${this.apiUrl}${id}/`,
      {
        headers: this.getHeaders()
      }
    );
  }

  deleteSavedList(id: number): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}${id}/`,
      {
        headers: this.getHeaders()
      }
    );
  }

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');

    return new HttpHeaders({
      Authorization: `Bearer ${token}`
    });
  }
}