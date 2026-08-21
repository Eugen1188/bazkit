import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { RegisterData } from '../models/user';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss'
})
export class RegisterComponent {
  private authService =
    inject(AuthService);

  private router =
    inject(Router);

  registerData: RegisterData = {
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    password2: ''
  };

  showPassword = false;
  showConfirmPassword = false;

  errorMessage = '';

  isLoading = false;

  togglePassword(): void {
    this.showPassword =
      !this.showPassword;
  }

  toggleConfirmPassword(): void {
    this.showConfirmPassword =
      !this.showConfirmPassword;
  }

  hasMinimumLength(): boolean {
    return (
      this.registerData.password.length >=
      8
    );
  }

  hasLetter(): boolean {
    return (
      /[A-Za-zÄÖÜäöüß]/.test(
        this.registerData.password
      )
    );
  }

  hasNumber(): boolean {
    return (
      /\d/.test(
        this.registerData.password
      )
    );
  }

  isPasswordValid(): boolean {
    return (
      this.hasMinimumLength() &&
      this.hasLetter() &&
      this.hasNumber()
    );
  }

  onRegister(): void {
    this.errorMessage = '';

    if (!this.isPasswordValid()) {
      this.errorMessage =
        'Bitte erfülle alle Passwort-Anforderungen.';
      return;
    }

    if (
      this.registerData.password !==
      this.registerData.password2
    ) {
      this.errorMessage =
        'Die Passwörter stimmen nicht überein.';
      return;
    }

    const payload = {
      first_name:
        this.registerData.first_name
          .trim(),

      last_name:
        this.registerData.last_name
          .trim(),

      email:
        this.registerData.email
          .trim()
          .toLowerCase(),

      password:
        this.registerData.password,

      password2:
        this.registerData.password2
    };

    this.isLoading = true;

    this.authService
      .register(payload)
      .subscribe({
        next: () => {
          this.isLoading = false;

          this.router.navigate(
            ['/'],
            {
              state: {
                registrationSuccess:
                  true
              }
            }
          );
        },

        error: error => {
          this.isLoading = false;

          console.error(
            'Registrierung fehlgeschlagen:',
            error
          );

          const response =
            error.error;

          if (response?.email) {
            this.errorMessage =
              Array.isArray(response.email)
                ? response.email[0]
                : response.email;

            return;
          }

          if (response?.password) {
            this.errorMessage =
              Array.isArray(response.password)
                ? response.password[0]
                : response.password;

            return;
          }

          if (response?.password2) {
            this.errorMessage =
              Array.isArray(response.password2)
                ? response.password2[0]
                : response.password2;

            return;
          }

          if (
            Array.isArray(
              response?.non_field_errors
            )
          ) {
            this.errorMessage =
              response.non_field_errors[0];

            return;
          }

          this.errorMessage =
            'Registrierung fehlgeschlagen. Bitte überprüfe deine Angaben.';
        }
      });
  }

  goBack(): void {
    this.router.navigate(['/']);
  }

  goToLogin(
    event: Event
  ): void {
    event.preventDefault();

    this.router.navigate(['/']);
  }
}