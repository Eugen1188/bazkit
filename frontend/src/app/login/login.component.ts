import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../services/auth.service';

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

  private authService = inject(AuthService);
  private router = inject(Router);

  constructor() {
    const navigation =
      this.router.getCurrentNavigation();

    const state =
      navigation?.extras.state as
        | {
            registrationSuccess?: boolean;
          }
        | undefined;

    if (state?.registrationSuccess) {
      this.successMessage =
        'Registrierung erfolgreich! Du kannst dich jetzt anmelden.';
    }
  }

  togglePassword(): void {
    this.showPassword =
      !this.showPassword;
  }

  onLogin(): void {
    this.errorMessage = '';
    this.successMessage = '';

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
          this.isLoading = false;

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

          this.router.navigate([
            '/main'
          ]);
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
            this.errorMessage =
              'E-Mail oder Passwort ist falsch.';
            return;
          }

          this.errorMessage =
            'Anmeldung fehlgeschlagen. Bitte versuche es erneut.';
        },
      });
  }
}