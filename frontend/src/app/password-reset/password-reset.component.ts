import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { BrandLogoComponent } from '../components/brand-logo/brand-logo.component';
import { AuthService } from '../services/auth.service';


@Component({
  selector: 'app-password-reset',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, BrandLogoComponent],
  templateUrl: './password-reset.component.html',
  styleUrl: './password-reset.component.scss',
})
export class PasswordResetComponent {
  email = '';
  newPassword = '';
  repeatedPassword = '';
  isLoading = false;
  isComplete = false;
  message = '';

  private readonly uid: string;
  private readonly token: string;
  readonly confirmationMode: boolean;

  constructor(
    route: ActivatedRoute,
    private readonly authService: AuthService,
  ) {
    this.uid = route.snapshot.queryParamMap.get('uid')?.trim() ?? '';
    this.token = route.snapshot.queryParamMap.get('token')?.trim() ?? '';
    this.confirmationMode = Boolean(this.uid && this.token);
  }

  submit(): void {
    if (this.isLoading) return;
    this.message = '';

    if (!this.confirmationMode) {
      this.requestLink();
      return;
    }
    if (this.newPassword !== this.repeatedPassword) {
      this.message = 'Die Passwörter stimmen nicht überein.';
      return;
    }
    if (this.newPassword.length < 8 || !/[A-Za-zÄÖÜäöüß]/.test(this.newPassword) || !/\d/.test(this.newPassword)) {
      this.message = 'Nutze mindestens 8 Zeichen sowie einen Buchstaben und eine Zahl.';
      return;
    }

    this.isLoading = true;
    this.authService.confirmPasswordReset({
      uid: this.uid,
      token: this.token,
      new_password: this.newPassword,
      new_password2: this.repeatedPassword,
    }).subscribe({
      next: response => {
        this.isLoading = false;
        this.isComplete = true;
        this.message = response.message;
      },
      error: error => {
        this.isLoading = false;
        this.message = this.apiError(error, 'Der Link ist ungültig oder abgelaufen.');
      },
    });
  }

  private requestLink(): void {
    if (!this.email.trim()) return;
    this.isLoading = true;
    this.authService.requestPasswordReset(this.email).subscribe({
      next: response => {
        this.isLoading = false;
        this.isComplete = true;
        this.message = response.message;
      },
      error: error => {
        this.isLoading = false;
        this.message = this.apiError(
          error,
          'Der Link konnte momentan nicht versendet werden.'
        );
      },
    });
  }

  private apiError(error: unknown, fallback: string): string {
    const response = error as {
      error?: { detail?: string; new_password?: string[] } | string;
    };
    if (typeof response?.error === 'string') return response.error;
    return response?.error?.detail || response?.error?.new_password?.[0] || fallback;
  }
}
