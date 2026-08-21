import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { RegisterData } from '../models/user';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss',
})
export class RegisterComponent {

  private authService = inject(AuthService);
  private router = inject(Router);

  registerData: RegisterData = {
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    password2: '',
  };

  showPassword = false;
  showConfirmPassword = false;

  errorMessage = '';
  isLoading = false;

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  toggleConfirmPassword(): void {
    this.showConfirmPassword = !this.showConfirmPassword;
  }

  get hasMinLength(): boolean {
    return this.registerData.password.length >= 8;
  }

  get hasLetter(): boolean {
    return /[A-Za-zÄÖÜäöüß]/.test(
      this.registerData.password
    );
  }

  get hasNumber(): boolean {
    return /\d/.test(this.registerData.password);
  }

  get isPasswordValid(): boolean {
    return (
      this.hasMinLength &&
      this.hasLetter &&
      this.hasNumber
    );
  }

  get passwordsMatch(): boolean {
    return (
      this.registerData.password.length > 0 &&
      this.registerData.password ===
        this.registerData.password2
    );
  }

  onRegister(): void {
    this.errorMessage = '';

    if (!this.isPasswordValid) {
      this.errorMessage =
        'Das Passwort erfüllt noch nicht alle Anforderungen.';
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
      first_name: this.registerData.first_name.trim(),
      last_name: this.registerData.last_name.trim(),

      // E-Mail immer normalisieren
      email: this.registerData.email
        .trim()
        .toLowerCase(),

      password: this.registerData.password,
      password2: this.registerData.password2,
    };

    this.isLoading = true;

    this.authService.register(payload).subscribe({

      next: (response) => {
        this.isLoading = false;

        console.log(
          'Erfolgreich registriert:',
          response
        );

        this.router.navigate(
          ['/'],
          {
            state: {
              registrationSuccess: true,
            },
          }
        );
      },

      error: (error) => {
        this.isLoading = false;

        console.error(
          'Registrierung fehlgeschlagen:',
          error
        );

        if (error.status === 0) {
          this.errorMessage =
            'Der Server ist momentan nicht erreichbar. Bitte versuche es später erneut.';
          return;
        }

        if (error.error?.email) {
          this.errorMessage =
            this.getErrorText(error.error.email);
          return;
        }

        if (error.error?.password) {
          this.errorMessage =
            this.getErrorText(error.error.password);
          return;
        }

        if (error.error?.password2) {
          this.errorMessage =
            this.getErrorText(error.error.password2);
          return;
        }

        if (error.error?.first_name) {
          this.errorMessage =
            this.getErrorText(error.error.first_name);
          return;
        }

        if (error.error?.last_name) {
          this.errorMessage =
            this.getErrorText(error.error.last_name);
          return;
        }

        if (error.error?.non_field_errors) {
          this.errorMessage =
            this.getErrorText(
              error.error.non_field_errors
            );
          return;
        }

        this.errorMessage =
          'Registrierung fehlgeschlagen. Bitte überprüfe deine Eingaben.';
      },
    });
  }

  goToLogin(): void {
    this.router.navigate(['/']);
  }

  private getErrorText(error: unknown): string {
    if (Array.isArray(error)) {
      return error.join(' ');
    }

    if (typeof error === 'string') {
      return error;
    }

    return 'Es ist ein Fehler aufgetreten.';
  }
}