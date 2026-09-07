import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../../services/auth.service';
import {
  SavedListInvitePreview,
  SavedListService
} from '../../services/saved-list.service';


@Component({
  selector: 'app-saved-list-invite',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './saved-list-invite.component.html',
  styleUrl: './saved-list-invite.component.scss'
})
export class SavedListInviteComponent implements OnInit {
  preview: SavedListInvitePreview | null = null;
  token = '';
  isLoading = true;
  isAccepting = false;
  errorMessage = '';

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly authService: AuthService,
    private readonly savedListService: SavedListService
  ) {}

  ngOnInit(): void {
    this.token = this.route.snapshot.paramMap.get('token')?.trim() ?? '';
    if (!this.token) {
      this.errorMessage = 'Im Einladungslink fehlt der Einladungscode.';
      this.isLoading = false;
      return;
    }
    this.savedListService.getInvitation(this.token).subscribe({
      next: preview => {
        this.preview = preview;
        this.isLoading = false;
      },
      error: error => {
        this.errorMessage = error?.error?.detail || 'Diese Einladung wurde nicht gefunden.';
        this.isLoading = false;
      }
    });
  }

  get isLoggedIn(): boolean {
    return this.authService.isLoggedIn();
  }

  get returnUrl(): string {
    return `/invite/${encodeURIComponent(this.token)}`;
  }

  accept(): void {
    if (!this.isLoggedIn) {
      void this.router.navigate(['/'], { queryParams: { returnUrl: this.returnUrl } });
      return;
    }
    this.isAccepting = true;
    this.errorMessage = '';
    this.savedListService.acceptInvitation(this.token).subscribe({
      next: response => {
        this.isAccepting = false;
        void this.router.navigate(['/main/saved-list', response.list_id]);
      },
      error: error => {
        this.isAccepting = false;
        this.errorMessage = error?.error?.detail || 'Die Einladung konnte nicht angenommen werden.';
      }
    });
  }

  openList(): void {
    if (this.preview?.can_open) {
      void this.router.navigate(['/main/saved-list', this.preview.list_id]);
    }
  }

  roleLabel(): string {
    return this.preview?.role === 'editor'
      ? 'Du kannst Produkte hinzufügen, bearbeiten und abhaken.'
      : 'Du kannst die Liste ansehen, aber nicht verändern.';
  }
}
