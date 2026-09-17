import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {
  catchError,
  finalize,
  Observable,
  of,
  shareReplay,
  tap,
  throwError,
  timeout
} from 'rxjs';
import { PriceSnapshot } from './product.service';
import { API_ROOT, apiEndpoint } from '../config/api.config';


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


export interface PendingSavedListToggle {
  listId: number;
  itemId: number;
  isChecked: boolean;
  queuedAt: string;
}

export interface PendingSavedListUpdate {
  listId: number;
  payload: CreateSavedListPayload;
  queuedAt: string;
}


@Injectable({ providedIn: 'root' })
export class SavedListService {
  private readonly apiRoot = API_ROOT;
  private readonly apiUrl = apiEndpoint('lists/saved-lists/');
  private readonly cacheLifetimeMs = 60_000;
  private cacheSession = '';
  private cacheExpiresAt = 0;
  private cacheRevision = 0;
  private cachedLists: SavedList[] | null = null;
  private readonly cachedDetails = new Map<number, SavedList>();
  private inFlightRequest: Observable<SavedList[]> | null = null;


  constructor(private readonly http: HttpClient) {
    window.addEventListener('bazkit:logout', () => this.clearOfflineData());
  }


  private invalidateListCache(): void {
    this.cacheRevision += 1;
    this.cacheExpiresAt = 0;
    this.cachedLists = null;
    this.inFlightRequest = null;
  }

  private ensureSession(): void {
    const session = localStorage.getItem('access_token') ?? '';
    if (session === this.cacheSession) return;
    this.cacheSession = session;
    this.invalidateListCache();
    this.cachedDetails.clear();
  }

  private sessionSubject(token = this.cacheSession): string {
    if (!token) return 'anonymous';
    try {
      const payload = token.split('.')[1]
        .replace(/-/g, '+')
        .replace(/_/g, '/');
      const paddedPayload = payload.padEnd(Math.ceil(payload.length / 4) * 4, '=');
      const decoded = JSON.parse(atob(paddedPayload)) as { user_id?: number | string; sub?: string };
      return String(decoded.user_id ?? decoded.sub ?? 'session');
    } catch {
      return 'session';
    }
  }

  private detailCacheKey(id: number): string {
    return `bazkit:saved-list:${this.sessionSubject()}:${id}`;
  }

  private listOverviewCacheKey(): string {
    return `bazkit:saved-lists:${this.sessionSubject()}`;
  }

  private toggleQueueKey(): string {
    return `bazkit:saved-list-toggles:${this.sessionSubject()}`;
  }

  private updateQueueKey(): string {
    return `bazkit:saved-list-updates:${this.sessionSubject()}`;
  }

  private cacheSavedList(list: SavedList): void {
    this.cachedDetails.set(list.id, list);
    try {
      localStorage.setItem(this.detailCacheKey(list.id), JSON.stringify(list));
    } catch {
      // The in-memory copy remains available if browser storage is unavailable.
    }
  }


  createSavedList(payload: CreateSavedListPayload): Observable<SavedList> {
    return this.http.post<SavedList>(this.apiUrl, payload).pipe(
      tap(() => this.invalidateListCache())
    );
  }


  getSavedLists(forceRefresh = false): Observable<SavedList[]> {
    const session = localStorage.getItem('access_token') ?? '';
    this.ensureSession();

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

    const offlineLists = this.readSavedListOverview();
    if (!navigator.onLine && offlineLists) {
      this.cachedLists = offlineLists;
      return of(offlineLists);
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
          this.writeSavedListOverview(lists);
        }
      }),
      catchError(error => {
        const fallback = this.readSavedListOverview();
        if (fallback && (error?.status === 0 || error?.name === 'TimeoutError')) {
          this.cachedLists = fallback;
          return of(fallback);
        }
        return throwError(() => error);
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
    this.ensureSession();
    return this.http.get<SavedList>(`${this.apiUrl}${id}/`).pipe(
      timeout({ first: 15_000 }),
      tap(list => this.cacheSavedList(list))
    );
  }

  getCachedSavedList(id: number): SavedList | null {
    this.ensureSession();
    const memoryCopy = this.cachedDetails.get(id);
    if (memoryCopy) return memoryCopy;
    try {
      const stored = localStorage.getItem(this.detailCacheKey(id));
      if (!stored) return null;
      const list = JSON.parse(stored) as SavedList;
      if (list.id !== id || !Array.isArray(list.items)) return null;
      this.cachedDetails.set(id, list);
      return list;
    } catch {
      return null;
    }
  }

  getPendingToggles(listId: number): PendingSavedListToggle[] {
    this.ensureSession();
    try {
      const stored = localStorage.getItem(this.toggleQueueKey());
      const queue = stored ? JSON.parse(stored) as PendingSavedListToggle[] : [];
      return Array.isArray(queue)
        ? queue.filter(item => item.listId === listId)
        : [];
    } catch {
      return [];
    }
  }

  queueSavedListToggle(listId: number, itemId: number, isChecked: boolean): void {
    this.ensureSession();
    const queue = this.readToggleQueue().filter(
      item => item.listId !== listId || item.itemId !== itemId
    );
    queue.push({ listId, itemId, isChecked, queuedAt: new Date().toISOString() });
    this.writeToggleQueue(queue);

    const cached = this.getCachedSavedList(listId);
    const item = cached?.items?.find(entry => entry.id === itemId);
    if (cached && item) {
      item.is_checked = isChecked;
      this.cacheSavedList(cached);
      this.updateOfflineOverview(cached);
    }
  }

  removePendingToggle(listId: number, itemId: number): void {
    const queue = this.readToggleQueue().filter(
      item => item.listId !== listId || item.itemId !== itemId
    );
    this.writeToggleQueue(queue);
  }

  getPendingUpdate(listId: number): PendingSavedListUpdate | null {
    this.ensureSession();
    return this.readUpdateQueue().find(update => update.listId === listId) ?? null;
  }

  queueSavedListUpdate(listId: number, payload: CreateSavedListPayload): void {
    this.ensureSession();
    const queue = this.readUpdateQueue().filter(update => update.listId !== listId);
    const storedPayload = JSON.parse(JSON.stringify(payload)) as CreateSavedListPayload;
    queue.push({ listId, payload: storedPayload, queuedAt: new Date().toISOString() });
    this.writeUpdateQueue(queue);

    const cached = this.getCachedSavedList(listId);
    if (!cached) return;
    const existingById = new Map((cached.items ?? []).map(item => [item.id, item]));
    cached.title = storedPayload.title;
    cached.items = storedPayload.items.map(item => ({
      ...existingById.get(item.id),
      ...item,
    }));
    cached.item_count = cached.items.length;
    cached.checked_count = cached.items.filter(item => item.is_checked).length;
    cached.updated_at = new Date().toISOString();
    this.cacheSavedList(cached);
    this.updateOfflineOverview(cached);
  }

  removePendingUpdate(listId: number): void {
    this.writeUpdateQueue(
      this.readUpdateQueue().filter(update => update.listId !== listId)
    );
  }

  applyPendingToggles(list: SavedList): SavedList {
    for (const pending of this.getPendingToggles(list.id)) {
      const item = list.items?.find(entry => entry.id === pending.itemId);
      if (item) item.is_checked = pending.isChecked;
    }
    this.cacheSavedList(list);
    return list;
  }

  applyPendingChanges(list: SavedList): SavedList {
    const pendingUpdate = this.getPendingUpdate(list.id);
    if (pendingUpdate) {
      const existingById = new Map((list.items ?? []).map(item => [item.id, item]));
      list.title = pendingUpdate.payload.title;
      list.items = pendingUpdate.payload.items.map(item => ({
        ...existingById.get(item.id),
        ...item,
      }));
      list.item_count = list.items.length;
      list.checked_count = list.items.filter(item => item.is_checked).length;
    }
    return this.applyPendingToggles(list);
  }

  private readToggleQueue(): PendingSavedListToggle[] {
    try {
      const stored = localStorage.getItem(this.toggleQueueKey());
      const queue = stored ? JSON.parse(stored) as PendingSavedListToggle[] : [];
      return Array.isArray(queue) ? queue : [];
    } catch {
      return [];
    }
  }

  private writeToggleQueue(queue: PendingSavedListToggle[]): void {
    try {
      if (queue.length) {
        localStorage.setItem(this.toggleQueueKey(), JSON.stringify(queue));
      } else {
        localStorage.removeItem(this.toggleQueueKey());
      }
    } catch {
      // A failed write is handled by the component's normal request fallback.
    }
  }

  private readUpdateQueue(): PendingSavedListUpdate[] {
    try {
      const stored = localStorage.getItem(this.updateQueueKey());
      const queue = stored ? JSON.parse(stored) as PendingSavedListUpdate[] : [];
      return Array.isArray(queue) ? queue : [];
    } catch {
      return [];
    }
  }

  private writeUpdateQueue(queue: PendingSavedListUpdate[]): void {
    try {
      if (queue.length) localStorage.setItem(this.updateQueueKey(), JSON.stringify(queue));
      else localStorage.removeItem(this.updateQueueKey());
    } catch {
      // The online save path remains available if browser storage is unavailable.
    }
  }

  private clearOfflineData(): void {
    const subject = this.sessionSubject();
    try {
      for (let index = localStorage.length - 1; index >= 0; index -= 1) {
        const key = localStorage.key(index);
        if (
          key?.startsWith(`bazkit:saved-list:${subject}:`)
          || key === `bazkit:saved-lists:${subject}`
          || key === `bazkit:saved-list-toggles:${subject}`
          || key === `bazkit:saved-list-updates:${subject}`
        ) {
          localStorage.removeItem(key);
        }
      }
    } catch {
      // In-memory data is still cleared when browser storage is unavailable.
    }
    this.cachedDetails.clear();
    this.cacheSession = '';
  }

  private readSavedListOverview(): SavedList[] | null {
    try {
      const stored = localStorage.getItem(this.listOverviewCacheKey());
      if (!stored) return null;
      const lists = JSON.parse(stored) as SavedList[];
      return Array.isArray(lists) ? lists : null;
    } catch {
      return null;
    }
  }

  private writeSavedListOverview(lists: SavedList[]): void {
    try {
      localStorage.setItem(this.listOverviewCacheKey(), JSON.stringify(lists));
    } catch {
      // Die Detailansichten bleiben auch bei vollem Browserspeicher nutzbar.
    }
  }

  private updateOfflineOverview(list: SavedList): void {
    const overview = this.readSavedListOverview();
    if (!overview) return;
    const index = overview.findIndex(item => item.id === list.id);
    if (index < 0) return;
    overview[index] = {
      ...overview[index],
      title: list.title,
      item_count: list.item_count,
      checked_count: list.checked_count,
      updated_at: list.updated_at,
    };
    this.writeSavedListOverview(overview);
  }


  updateSavedList(
    id: number,
    payload: CreateSavedListPayload
  ): Observable<SavedList> {
    return this.http.put<SavedList>(`${this.apiUrl}${id}/`, payload).pipe(
      tap(list => {
        this.cacheSavedList(list);
        this.invalidateListCache();
      })
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


}
