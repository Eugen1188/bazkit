import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {
  finalize,
  Observable,
  shareReplay
} from 'rxjs';


export interface UserProfile {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  pending_email?: string;
  email_verified?: boolean;
  avatar_url?: string | null;
  email_change_pending?: boolean;
  message?: string;
  date_joined?: string;
}


export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
  new_password2: string;
}

interface TokenRefreshResponse {
  access: string;
  refresh?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private apiUrl = this.getApiUrl();

  private refreshRequest: Observable<TokenRefreshResponse> | null = null;

  constructor(
    private http: HttpClient
  ) {}

  register(data: any): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/users/register/`,
      data
    );
  }

  login(data: any): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/users/login/`,
      data
    );
  }

  getMe(): Observable<UserProfile> {
    return this.http.get<UserProfile>(
      `${this.apiUrl}/users/me/`
    );
  }

  updateProfile(data: Pick<UserProfile, 'first_name' | 'last_name' | 'email'>): Observable<UserProfile> {
    return this.http.patch<UserProfile>(`${this.apiUrl}/users/me/`, data);
  }

  uploadAvatar(file: File): Observable<UserProfile> {
    const formData = new FormData();
    formData.append('avatar', file);
    return this.http.put<UserProfile>(`${this.apiUrl}/users/me/avatar/`, formData);
  }

  deleteAvatar(): Observable<UserProfile> {
    return this.http.delete<UserProfile>(`${this.apiUrl}/users/me/avatar/`);
  }

  verifyEmail(token: string): Observable<{ message: string; email: string }> {
    return this.http.post<{ message: string; email: string }>(
      `${this.apiUrl}/users/verify-email/`,
      { token }
    );
  }

  resendVerification(email: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `${this.apiUrl}/users/resend-verification/`,
      { email: email.trim().toLowerCase() }
    );
  }

  changePassword(data: ChangePasswordPayload): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `${this.apiUrl}/users/me/change-password/`,
      data
    );
  }

  deleteAccount(): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/users/me/`);
  }

  refreshToken(): Observable<TokenRefreshResponse> {
    if (this.refreshRequest) {
      return this.refreshRequest;
    }

    const refresh =
      localStorage.getItem('refresh_token');

    const request = this.http.post<TokenRefreshResponse>(
      `${this.apiUrl}/api/token/refresh/`,
      {
        refresh
      }
    ).pipe(
      finalize(() => {
        if (this.refreshRequest === request) {
          this.refreshRequest = null;
        }
      }),
      shareReplay({ bufferSize: 1, refCount: false })
    );

    this.refreshRequest = request;
    return request;
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem(
      'access_token'
    );
  }

  getCurrentUser(): UserProfile | null {
    const user =
      localStorage.getItem('user');

    if (!user) {
      return null;
    }

    try {
      return JSON.parse(user) as UserProfile;
    } catch {
      return null;
    }
  }

  storeCurrentUser(user: UserProfile): void {
    localStorage.setItem('user', JSON.stringify(user));
  }

  logout(): void {
    localStorage.removeItem(
      'access_token'
    );

    localStorage.removeItem(
      'refresh_token'
    );

    localStorage.removeItem(
      'user'
    );

    localStorage.removeItem(
      'bazkit_user_settings'
    );

    window.dispatchEvent(
      new Event('bazkit:logout')
    );
  }

  private getApiUrl(): string {
    return window.location.hostname === 'localhost'
      || window.location.hostname === '127.0.0.1'
      ? 'http://localhost:8000'
      : 'http://178.104.47.231:8000';
  }
}
