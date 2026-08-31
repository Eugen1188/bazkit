import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of, shareReplay, tap } from 'rxjs';

import {
  CommunityComment,
  CommunityCopyResponse,
  CommunityLikeResponse,
  CommunityPost,
  CommunityPostType,
  CommunityRatingResponse,
  CommunityShareOptions,
  CreateCommunityPostPayload,
  UpdateCommunityPostPayload
} from '../models/community.model';


@Injectable({ providedIn: 'root' })
export class CommunityService {
  private static readonly cacheLifetimeMs = 60_000;

  private readonly apiUrl = this.getApiUrl();
  private cacheSession = '';
  private readonly postCache = new Map<
    string,
    { expiresAt: number; posts: CommunityPost[] }
  >();
  private readonly postRequests = new Map<string, Observable<CommunityPost[]>>();


  constructor(private readonly http: HttpClient) {}


  private getApiUrl(): string {
    const hostname = window.location.hostname;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
    return isLocal
      ? 'http://localhost:8000/community/'
      : 'http://178.104.47.231:8000/community/';
  }


  private ensureSession(): void {
    const session = localStorage.getItem('access_token') ?? '';
    if (session === this.cacheSession) return;

    this.cacheSession = session;
    this.invalidatePostCache();
  }


  private invalidatePostCache(): void {
    this.postCache.clear();
    this.postRequests.clear();
  }


  getPosts(
    type: 'all' | CommunityPostType = 'all',
    search = ''
  ): Observable<CommunityPost[]> {
    this.ensureSession();
    const requestSession = this.cacheSession;

    const normalizedSearch = search.trim();
    const cacheKey = `${type}:${normalizedSearch.toLocaleLowerCase('de')}`;
    const cached = this.postCache.get(cacheKey);

    if (cached && Date.now() < cached.expiresAt) {
      return of(cached.posts);
    }

    const pending = this.postRequests.get(cacheKey);
    if (pending) return pending;

    let params = new HttpParams();
    if (type !== 'all') params = params.set('type', type);
    if (normalizedSearch) params = params.set('search', normalizedSearch);

    let request!: Observable<CommunityPost[]>;
    request = this.http.get<CommunityPost[]>(
      `${this.apiUrl}posts/`,
      { params }
    ).pipe(
      tap({
        next: posts => {
          if (
            this.cacheSession !== requestSession ||
            this.postRequests.get(cacheKey) !== request
          ) return;

          this.postCache.set(cacheKey, {
            posts,
            expiresAt: Date.now() + CommunityService.cacheLifetimeMs
          });
          this.postRequests.delete(cacheKey);
        },
        error: () => {
          if (this.postRequests.get(cacheKey) === request) {
            this.postRequests.delete(cacheKey);
          }
        }
      }),
      shareReplay({ bufferSize: 1, refCount: false })
    );

    this.postRequests.set(cacheKey, request);
    return request;
  }


  getPost(id: number): Observable<CommunityPost> {
    return this.http.get<CommunityPost>(`${this.apiUrl}posts/${id}/`);
  }


  createPost(payload: CreateCommunityPostPayload): Observable<CommunityPost> {
    return this.http.post<CommunityPost>(`${this.apiUrl}posts/`, payload).pipe(
      tap(() => this.invalidatePostCache())
    );
  }


  deletePost(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}posts/${id}/`).pipe(
      tap(() => this.invalidatePostCache())
    );
  }


  updatePost(
    id: number,
    payload: UpdateCommunityPostPayload
  ): Observable<CommunityPost> {
    return this.http.patch<CommunityPost>(
      `${this.apiUrl}posts/${id}/`,
      payload
    ).pipe(tap(() => this.invalidatePostCache()));
  }


  getShareOptions(): Observable<CommunityShareOptions> {
    return this.http.get<CommunityShareOptions>(`${this.apiUrl}share-options/`);
  }


  getComments(postId: number): Observable<CommunityComment[]> {
    return this.http.get<CommunityComment[]>(
      `${this.apiUrl}posts/${postId}/comments/`
    );
  }


  createComment(postId: number, content: string): Observable<CommunityComment> {
    return this.http.post<CommunityComment>(
      `${this.apiUrl}posts/${postId}/comments/`,
      { content }
    ).pipe(tap(() => this.invalidatePostCache()));
  }


  deleteComment(commentId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}comments/${commentId}/`).pipe(
      tap(() => this.invalidatePostCache())
    );
  }


  toggleLike(postId: number): Observable<CommunityLikeResponse> {
    return this.http.post<CommunityLikeResponse>(
      `${this.apiUrl}posts/${postId}/like/`,
      {}
    ).pipe(tap(() => this.invalidatePostCache()));
  }


  ratePost(postId: number, value: number): Observable<CommunityRatingResponse> {
    return this.http.post<CommunityRatingResponse>(
      `${this.apiUrl}posts/${postId}/rating/`,
      { value }
    ).pipe(tap(() => this.invalidatePostCache()));
  }


  copyPost(postId: number): Observable<CommunityCopyResponse> {
    return this.http.post<CommunityCopyResponse>(
      `${this.apiUrl}posts/${postId}/copy/`,
      {}
    );
  }
}
