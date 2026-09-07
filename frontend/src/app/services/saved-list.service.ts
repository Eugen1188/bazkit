import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {
  finalize,
  Observable,
  of,
  shareReplay,
  tap,
  timeout
} from 'rxjs';
import { PriceSnapshot } from './product.service';


export interface SavedListItem extends PriceSnapshot {
  id?: number;
  product?: number | null;
  product_name?: string;
  name: string;
  quantity: number;
  unit: string;
  note?: string;
  is_checked?: boolean;
  created_by_name?: string;
  checked_by_name?: string;
  checked_at?: string | null;
  updated_at?: string;
}


export type SavedListRole = 'owner' | 'editor' | 'viewer';


export interface SavedListMember {
  id: number | null;
  user_id: number;
  display_name: string;
  email: string;
  avatar_url?: string | null;
  role: SavedListRole;
  is_owner: boolean;
  joined_at?: string;
}


export interface SavedListInvitation {
  id: number;
  email: string;
  role: Exclude<SavedListRole, 'owner'>;
  created_at: string;
  expires_at: string;
  status: 'pending' | 'accepted' | 'expired' | 'revoked';
  invite_url: string;
  email_sent?: boolean;
}


export interface SavedListCollaboration {
  members: SavedListMember[];
  invitations: SavedListInvitation[];
  can_manage: boolean;
}


export interface SavedListInvitePreview {
  status: 'pending' | 'accepted' | 'expired' | 'revoked' | 'invalid';
  list_id: number;
  list_title: string;
  inviter_name: string;
  role: Exclude<SavedListRole, 'owner'>;
  expires_at: string;
  email_required: boolean;
  invited_email: string;
  can_open: boolean;
}


export interface SavedList {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  item_count: number;
  checked_count: number;
  member_count: number;
  access_role: SavedListRole;
  can_edit: boolean;
  is_owner: boolean;
  owner_name: string;
  estimated_total?: number | null;
  items?: SavedListItem[];
}


export interface CreateSavedListPayload {
  title: string;
  items: SavedListItem[];
}


@Injectable({ providedIn: 'root' })
export class SavedListService {
  private readonly apiRoot = this.getApiRoot();
  private readonly apiUrl = `${this.apiRoot}/lists/saved-lists/`;
  private readonly cacheLifetimeMs = 60_000;
  private cacheSession = '';
  private cacheExpiresAt = 0;
  private cacheRevision = 0;
  private cachedLists: SavedList[] | null = null;
  private inFlightRequest: Observable<SavedList[]> | null = null;


  constructor(private readonly http: HttpClient) {}


  private invalidateListCache(): void {
    this.cacheRevision += 1;
    this.cacheExpiresAt = 0;
    this.cachedLists = null;
    this.inFlightRequest = null;
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

    if (forceRefresh) {
      this.invalidateListCache();
    }

    if (
      !forceRefresh &&
      this.cachedLists &&
      Date.now() < this.cacheExpiresAt
    ) {
      return of(this.cachedLists);
    }

    if (!forceRefresh && this.inFlightRequest) {
      return this.inFlightRequest;
    }

    const revision = this.cacheRevision;
    const request = this.http.get<SavedList[]>(this.apiUrl).pipe(
      timeout({ first: 15_000 }),
      tap(lists => {
        if (
          revision === this.cacheRevision &&
          session === (localStorage.getItem('access_token') ?? '')
        ) {
          this.cachedLists = lists;
          this.cacheExpiresAt = Date.now() + this.cacheLifetimeMs;
        }
      }),
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


  getSavedList(id: number): Observable<SavedList> {
    return this.http.get<SavedList>(`${this.apiUrl}${id}/`).pipe(
      timeout({ first: 15_000 })
    );
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


  toggleSavedListItem(
    listId: number,
    itemId: number,
    isChecked: boolean
  ): Observable<SavedListItem> {
    return this.http.patch<SavedListItem>(
      `${this.apiUrl}${listId}/items/${itemId}/toggle/`,
      { is_checked: isChecked }
    ).pipe(tap(() => this.invalidateListCache()));
  }


  getCollaboration(listId: number): Observable<SavedListCollaboration> {
    return this.http.get<SavedListCollaboration>(
      `${this.apiUrl}${listId}/collaboration/`
    );
  }


  inviteToList(
    listId: number,
    email: string,
    role: Exclude<SavedListRole, 'owner'>
  ): Observable<SavedListInvitation> {
    return this.http.post<SavedListInvitation>(
      `${this.apiUrl}${listId}/collaboration/`,
      { email: email.trim().toLowerCase(), role }
    ).pipe(tap(() => this.invalidateListCache()));
  }


  updateInvitationRole(
    listId: number,
    invitationId: number,
    role: Exclude<SavedListRole, 'owner'>
  ): Observable<SavedListInvitation> {
    return this.http.patch<SavedListInvitation>(
      `${this.apiUrl}${listId}/invitations/${invitationId}/`,
      { role }
    );
  }


  revokeInvitation(listId: number, invitationId: number): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}${listId}/invitations/${invitationId}/`
    ).pipe(tap(() => this.invalidateListCache()));
  }


  updateMemberRole(
    listId: number,
    membershipId: number,
    role: Exclude<SavedListRole, 'owner'>
  ): Observable<SavedListMember> {
    return this.http.patch<SavedListMember>(
      `${this.apiUrl}${listId}/members/${membershipId}/`,
      { role }
    ).pipe(tap(() => this.invalidateListCache()));
  }


  removeMember(listId: number, membershipId: number): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}${listId}/members/${membershipId}/`
    ).pipe(tap(() => this.invalidateListCache()));
  }


  leaveList(listId: number): Observable<void> {
    return this.http.post<void>(
      `${this.apiUrl}${listId}/leave/`,
      {}
    ).pipe(tap(() => this.invalidateListCache()));
  }


  getInvitation(token: string): Observable<SavedListInvitePreview> {
    return this.http.get<SavedListInvitePreview>(
      `${this.apiRoot}/lists/saved-list-invitations/${encodeURIComponent(token)}/`
    );
  }


  acceptInvitation(token: string): Observable<{ message: string; list_id: number; role: string }> {
    return this.http.post<{ message: string; list_id: number; role: string }>(
      `${this.apiRoot}/lists/saved-list-invitations/${encodeURIComponent(token)}/`,
      {}
    ).pipe(tap(() => this.invalidateListCache()));
  }


  private getApiRoot(): string {
    return window.location.hostname === 'localhost'
      || window.location.hostname === '127.0.0.1'
      ? 'http://localhost:8000'
      : 'http://178.104.47.231:8000';
  }
}
