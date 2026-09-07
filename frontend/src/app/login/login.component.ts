import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { UserSettingsService } from '../services/user-settings.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  email = '';
  password = '';

  showPassword = false;

  errorMessage = '';
  successMessage = '';

  isLoading = false;
  isResending = false;
  showResendVerification = false;

  private authService = inject(AuthService);
  private userSettings = inject(UserSettingsService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  readonly returnUrl = this.safeReturnUrl(
    this.route.snapshot.queryParamMap.get('returnUrl')
      || sessionStorage.getItem('bazkit_post_auth_return_url')
  );

  constructor() {
    const navigation =
      this.router.getCurrentNavigation();

    const state =
      navigation?.extras.state as
        | {
            registrationSuccess?: boolean;
            registrationEmail?: string;
          }
        | undefined;

    if (state?.registrationSuccess) {
      this.email = state.registrationEmail ?? '';
      this.showResendVerification = true;
      this.successMessage =
        'Wir haben dir einen Bestätigungslink geschickt. Öffne ihn, bevor du dich anmeldest.';
    }
  }

  togglePassword(): void {
    this.showPassword =
      !this.showPassword;
  }

  onLogin(): void {
    this.errorMessage = '';
    this.successMessage = '';
    this.showResendVerification = false;

    const loginData = {
      email:
        this.email
          .trim()
          .toLowerCase(),

      password:
        this.password,
    };

    this.isLoading = true;

    this.authService
      .login(loginData)
      .subscribe({
        next: response => {
          localStorage.setItem(
            'access_token',
            response.access
          );

          localStorage.setItem(
            'refresh_token',
            response.refresh
          );

          localStorage.setItem(
            'user',
            JSON.stringify(
              response.user
            )
          );

          this.userSettings.load().subscribe({
            next: () => {
              this.isLoading = false;
              sessionStorage.removeItem('bazkit_post_auth_return_url');
              void this.router.navigateByUrl(this.returnUrl);
            },
            error: () => {
              // Die Anmeldung bleibt möglich; Standardwerte dienen als Fallback.
              this.isLoading = false;
              sessionStorage.removeItem('bazkit_post_auth_return_url');
              void this.router.navigateByUrl(this.returnUrl);
            },
          });
        },

        error: error => {
          this.isLoading = false;

          console.error(
            'Login fehlgeschlagen:',
            error
          );

          if (error.status === 0) {
            this.errorMessage =
              'Der Server ist momentan nicht erreichbar.';
            return;
          }

          if (
            error.status === 400 ||
            error.status === 401
          ) {
            const response = error.error;
            const code = Array.isArray(response?.code)
              ? response.code[0]
              : response?.code;
            if (code === 'email_not_verified') {
              this.errorMessage = 'Bitte bestätige zuerst deine E-Mail-Adresse.';
              this.showResendVerification = true;
              return;
            }
            this.errorMessage =
              'E-Mail oder Passwort ist falsch.';
            return;
          }

          this.errorMessage =
            'Anmeldung fehlgeschlagen. Bitte versuche es erneut.';
        },
      });
  }

  resendVerification(): void {
    if (!this.email.trim() || this.isResending) return;
    this.isResending = true;
    this.errorMessage = '';
    this.successMessage = '';
    this.authService.resendVerification(this.email).subscribe({
      next: response => {
        this.isResending = false;
        this.successMessage = response.message;
      },
      error: () => {
        this.isResending = false;
        this.errorMessage = 'Die Bestätigungs-E-Mail konnte momentan nicht versendet werden.';
      },
    });
  }

  private safeReturnUrl(value: string | null): string {
    return value?.startsWith('/') && !value.startsWith('//')
      ? value
      : '/main/home';
  }
}
