import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface SavedList {
  id: number;
  title: string;
  created_at: string;
  item_count: number;
}

@Injectable({
  providedIn: 'root',
})
export class SavedListService {

  private apiUrl = 'http://178.104.47.231:8000/lists/saved-lists/';

  constructor(private http: HttpClient) {}

  createSavedList(title: string): Observable<SavedList> {
  return this.http.post<SavedList>(
    this.apiUrl,
    { title },
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

  deleteSavedList(id: number): Observable<any> {
    return this.http.delete(
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