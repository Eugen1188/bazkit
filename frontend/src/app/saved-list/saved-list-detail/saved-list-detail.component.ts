import { CommonModule } from '@angular/common';
import { Component, HostListener, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription, timer } from 'rxjs';

import {
  SavedList,
  SavedListCollaboration,
  SavedListInvitation,
  SavedListItem,
  SavedListMember,
  SavedListRole,
  SavedListService
} from '../../services/saved-list.service';
import { ListShareService } from '../../services/list-share.service';


@Component({
  selector: 'app-saved-list-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './saved-list-detail.component.html',
  styleUrl: './saved-list-detail.component.scss'
})
export class SavedListDetailComponent implements OnInit, OnDestroy {
  savedList: SavedList | null = null;
  collaboration: SavedListCollaboration | null = null;

  isLoading = true;
  isRefreshing = false;
  isMenuOpen = false;
  isCollaborationOpen = false;
  isCollaborationLoading = false;
  isInviting = false;
  errorMessage = '';
  collaborationError = '';
  shareMessage = '';
  inviteEmail = '';
  inviteRole: Exclude<SavedListRole, 'owner'> = 'editor';
  lastInviteUrl = '';
  updatingItemIds = new Set<number>();

  private listId = 0;
  private pollingSubscription?: Subscription;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly savedListService: SavedListService,
    private readonly listShareService: ListShareService
  ) {}

  ngOnInit(): void {
    this.listId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.listId) {
      this.errorMessage = 'Die Liste konnte nicht gefunden werden.';
      this.isLoading = false;
      return;
    }

    this.loadSavedList();
    this.pollingSubscription = timer(3000, 3000).subscribe(() => {
      if (!document.hidden && !this.isRefreshing && !this.isInviting) {
        this.refreshSavedList();
      }
    });
  }

  ngOnDestroy(): void {
    this.pollingSubscription?.unsubscribe();
  }

  loadSavedList(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.savedListService.getSavedList(this.listId).subscribe({
      next: list => {
        this.savedList = list;
        this.isLoading = false;
        if (this.route.snapshot.queryParamMap.get('collaborate') === '1') {
          this.openCollaboration();
        }
      },
      error: error => {
        console.error('Liste konnte nicht geladen werden:', error);
        this.errorMessage = 'Die Liste konnte nicht geladen werden.';
        this.isLoading = false;
      }
    });
  }

  private refreshSavedList(): void {
    this.isRefreshing = true;
    this.savedListService.getSavedList(this.listId).subscribe({
      next: list => {
        this.savedList = list;
        this.isRefreshing = false;
      },
      error: error => {
        this.isRefreshing = false;
        if (error?.status === 403 || error?.status === 404) {
          this.showMessage('Du hast keinen Zugriff mehr auf diese Liste.');
          void this.router.navigate(['/main/saved-list']);
        }
      }
    });
  }

  toggleMenu(event: MouseEvent): void {
    event.stopPropagation();
    this.isMenuOpen = !this.isMenuOpen;
  }

  @HostListener('document:click')
  closeMenu(): void {
    this.isMenuOpen = false;
  }

  @HostListener('document:keydown.escape')
  closeDialog(): void {
    if (this.isCollaborationOpen) this.isCollaborationOpen = false;
  }

  editList(): void {
    if (!this.savedList?.can_edit) return;
    this.isMenuOpen = false;
    void this.router.navigate(['/main/saved-list', this.savedList.id, 'edit']);
  }

  editItem(_item: SavedListItem): void {
    this.editList();
  }

  toggleItem(item: SavedListItem): void {
    if (!this.savedList?.can_edit || !item.id || this.updatingItemIds.has(item.id)) return;
    const previous = Boolean(item.is_checked);
    item.is_checked = !previous;
    this.updatingItemIds.add(item.id);
    this.savedListService.toggleSavedListItem(this.savedList.id, item.id, !previous).subscribe({
      next: updated => {
        Object.assign(item, updated);
        this.updatingItemIds.delete(item.id!);
        this.refreshSavedList();
      },
      error: error => {
        item.is_checked = previous;
        this.updatingItemIds.delete(item.id!);
        this.showMessage(this.apiError(error, 'Das Produkt konnte nicht aktualisiert werden.'));
      }
    });
  }

  async shareList(): Promise<void> {
    if (!this.savedList) return;
    this.isMenuOpen = false;
    try {
      const result = await this.listShareService.shareList(
        this.savedList.title,
        (this.savedList.items ?? []).map(item => ({
          name: item.name || item.product_name || '',
          quantity: item.quantity,
          unit: item.unit,
          note: item.note,
          isChecked: Boolean(item.is_checked)
        }))
      );
      if (result === 'copied') this.showMessage('Eine Kopie der Liste wurde kopiert.');
    } catch (error) {
      console.error('Liste konnte nicht geteilt werden:', error);
      this.showMessage('Die Liste konnte nicht geteilt werden.');
    }
  }

  deleteList(): void {
    if (!this.savedList?.is_owner) return;
    this.isMenuOpen = false;
    if (!confirm(`Möchtest du „${this.savedList.title}“ wirklich löschen?`)) return;
    this.savedListService.deleteSavedList(this.savedList.id).subscribe({
      next: () => void this.router.navigate(['/main/saved-list']),
      error: error => {
        console.error('Liste konnte nicht gelöscht werden:', error);
        this.errorMessage = 'Die Liste konnte nicht gelöscht werden.';
      }
    });
  }

  leaveList(): void {
    if (!this.savedList || this.savedList.is_owner) return;
    this.isMenuOpen = false;
    if (!confirm(`Möchtest du die gemeinsame Liste „${this.savedList.title}“ verlassen?`)) return;
    this.savedListService.leaveList(this.savedList.id).subscribe({
      next: () => void this.router.navigate(['/main/saved-list']),
      error: error => this.showMessage(this.apiError(error, 'Die Liste konnte nicht verlassen werden.'))
    });
  }

  deleteItem(item: SavedListItem): void {
    if (!this.savedList?.can_edit || !item.id) return;
    if (!confirm(`Möchtest du „${this.getItemName(item)}“ aus der Liste entfernen?`)) return;
    this.savedListService.deleteSavedListItem(this.savedList.id, item.id).subscribe({
      next: () => this.refreshSavedList(),
      error: error => this.showMessage(this.apiError(error, 'Das Produkt konnte nicht entfernt werden.'))
    });
  }

  openCollaboration(): void {
    if (!this.savedList) return;
    this.isMenuOpen = false;
    this.isCollaborationOpen = true;
    this.loadCollaboration();
  }

  loadCollaboration(): void {
    this.isCollaborationLoading = true;
    this.collaborationError = '';
    this.savedListService.getCollaboration(this.listId).subscribe({
      next: collaboration => {
        this.collaboration = collaboration;
        this.isCollaborationLoading = false;
      },
      error: error => {
        this.collaborationError = this.apiError(error, 'Die Freigaben konnten nicht geladen werden.');
        this.isCollaborationLoading = false;
      }
    });
  }

  createInvitation(asLink = false): void {
    if (!this.savedList?.is_owner || this.isInviting) return;
    const email = asLink ? '' : this.inviteEmail.trim();
    if (!asLink && !email) {
      this.collaborationError = 'Bitte gib eine E-Mail-Adresse ein.';
      return;
    }
    this.isInviting = true;
    this.collaborationError = '';
    this.savedListService.inviteToList(this.savedList.id, email, this.inviteRole).subscribe({
      next: invitation => {
        this.isInviting = false;
        this.inviteEmail = '';
        this.lastInviteUrl = invitation.invite_url;
        this.loadCollaboration();
        const message = email && invitation.email_sent
          ? 'Die Einladung wurde per E-Mail versendet.'
          : email
            ? 'Der Link wurde erstellt. Die E-Mail konnte nicht versendet werden – kopiere den Link manuell.'
            : 'Der Einladungslink wurde erstellt.';
        this.showMessage(message);
      },
      error: error => {
        this.isInviting = false;
        this.collaborationError = this.apiError(error, 'Die Einladung konnte nicht erstellt werden.');
      }
    });
  }

  async copyInviteLink(url = this.lastInviteUrl): Promise<void> {
    if (!url) return;
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(url);
        this.showMessage('Einladungslink wurde kopiert.');
        return;
      } catch {
        // Auf HTTP-Seiten ist die moderne Zwischenablage häufig gesperrt.
      }
    }
    const input = document.createElement('textarea');
    input.value = url;
    input.setAttribute('readonly', '');
    input.style.position = 'fixed';
    input.style.left = '-9999px';
    document.body.appendChild(input);
    input.select();
    let copied = false;
    try {
      copied = document.execCommand('copy');
    } catch {
      copied = false;
    } finally {
      document.body.removeChild(input);
    }
    this.showMessage(copied ? 'Einladungslink wurde kopiert.' : 'Der Link konnte nicht kopiert werden.');
  }

  updateMemberRole(member: SavedListMember, role: Exclude<SavedListRole, 'owner'>): void {
    if (!this.savedList?.is_owner || member.id === null) return;
    this.savedListService.updateMemberRole(this.savedList.id, member.id, role).subscribe({
      next: () => this.loadCollaboration(),
      error: error => this.collaborationError = this.apiError(error, 'Die Berechtigung konnte nicht geändert werden.')
    });
  }

  removeMember(member: SavedListMember): void {
    if (!this.savedList?.is_owner || member.id === null) return;
    if (!confirm(`${member.display_name} wirklich aus der Liste entfernen?`)) return;
    this.savedListService.removeMember(this.savedList.id, member.id).subscribe({
      next: () => {
        this.loadCollaboration();
        this.refreshSavedList();
      },
      error: error => this.collaborationError = this.apiError(error, 'Die Person konnte nicht entfernt werden.')
    });
  }

  updateInvitationRole(invitation: SavedListInvitation, role: Exclude<SavedListRole, 'owner'>): void {
    if (!this.savedList?.is_owner) return;
    this.savedListService.updateInvitationRole(this.savedList.id, invitation.id, role).subscribe({
      next: () => this.loadCollaboration(),
      error: error => this.collaborationError = this.apiError(error, 'Die Berechtigung konnte nicht geändert werden.')
    });
  }

  revokeInvitation(invitation: SavedListInvitation): void {
    if (!this.savedList?.is_owner) return;
    this.savedListService.revokeInvitation(this.savedList.id, invitation.id).subscribe({
      next: () => this.loadCollaboration(),
      error: error => this.collaborationError = this.apiError(error, 'Die Einladung konnte nicht zurückgezogen werden.')
    });
  }

  getItemName(item: SavedListItem): string {
    return item.name || item.product_name || 'Produkt';
  }

  memberInitial(member: SavedListMember): string {
    return member.display_name.charAt(0).toUpperCase() || '?';
  }

  roleLabel(role: SavedListRole): string {
    if (role === 'owner') return 'Eigentümer';
    return role === 'editor' ? 'Kann bearbeiten' : 'Kann ansehen';
  }

  get itemCount(): number {
    return this.savedList?.items?.length ?? 0;
  }

  get checkedCount(): number {
    return (this.savedList?.items ?? []).filter(item => item.is_checked).length;
  }

  formatDate(date: string): string {
    return new Intl.DateTimeFormat('de-DE', {
      day: '2-digit', month: '2-digit', year: 'numeric'
    }).format(new Date(date));
  }

  private showMessage(message: string): void {
    this.shareMessage = message;
    window.setTimeout(() => {
      if (this.shareMessage === message) this.shareMessage = '';
    }, 3500);
  }

  private apiError(error: unknown, fallback: string): string {
    const response = error as {
      error?: { detail?: string; email?: string[]; role?: string[] } | string
    };
    if (typeof response.error === 'string') return response.error;
    return response.error?.detail
      || response.error?.email?.[0]
      || response.error?.role?.[0]
      || fallback;
  }
}
