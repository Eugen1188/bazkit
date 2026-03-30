import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private apiUrl = 'http://178.104.47.231:8000';

  constructor(private http: HttpClient) {}

  register(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/users/register/`, data);
  }

  login(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/users/login/`, data);
  }

  getMe(): Observable<any> {
    return this.http.get(`${this.apiUrl}/users/me/`);
  }
}