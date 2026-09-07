import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { AuthService } from '../services/auth.service';


type VerificationState = 'loading' | 'success' | 'error';


@Component({
  selector: 'app-verify-email',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './verify-email.component.html',
  styleUrl: './verify-email.component.scss',
})
export class VerifyEmailComponent implements OnInit {
  state: VerificationState = 'loading';
  message = 'Deine E-Mail-Adresse wird bestätigt…';
  resendEmail = '';
  isResending = false;
  resendMessage = '';

  constructor(
    private readonly route: ActivatedRoute,
    private readonly authService: AuthService,
  ) {}

  ngOnInit(): void {
    const token = this.route.snapshot.queryParamMap.get('token')?.trim() ?? '';
    if (!token) {
      this.state = 'error';
      this.message = 'Im Link fehlt der Bestätigungscode.';
      return;
    }

    this.authService.verifyEmail(token).subscribe({
      next: response => {
        const currentUser = this.authService.getCurrentUser();
        if (currentUser) {
          this.authService.storeCurrentUser({
            ...currentUser,
            email: response.email,
            pending_email: '',
            email_verified: true,
          });
        }
        this.state = 'success';
        this.message = response.message;
        this.resendEmail = response.email;
      },
      error: error => {
        this.state = 'error';
        this.message = this.apiError(
          error,
          'Der Bestätigungslink ist ungültig oder abgelaufen.'
        );
      },
    });
  }

  resend(): void {
    if (!this.resendEmail.trim() || this.isResending) return;
    this.isResending = true;
    this.resendMessage = '';
    this.authService.resendVerification(this.resendEmail).subscribe({
      next: response => {
        this.isResending = false;
        this.resendMessage = response.message;
      },
      error: error => {
        this.isResending = false;
        this.resendMessage = this.apiError(
          error,
          'Die E-Mail konnte momentan nicht versendet werden.'
        );
      },
    });
  }

  private apiError(error: unknown, fallback: string): string {
    const response = error as { error?: { detail?: string } | string };
    if (typeof response?.error === 'string') return response.error;
    return response?.error?.detail || fallback;
  }
}
