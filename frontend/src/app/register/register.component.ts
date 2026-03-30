import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../services/auth.service';
import { RegisterData } from '../models/user';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss'
})
export class RegisterComponent {

  private authService = inject(AuthService);

  registerData: RegisterData = {
    email: '',
    password: '',
    password2: ''
  };

  showPassword = false;
  showConfirmPassword = false;
  errorMessage = '';
  successMessage = '';
  isLoading = false;

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  toggleConfirmPassword(): void {
    this.showConfirmPassword = !this.showConfirmPassword;
  }

  onRegister(): void {
    this.errorMessage = '';
    this.successMessage = '';
    if (this.registerData.password !== this.registerData.password2) {
      this.errorMessage = 'Die Passwörter stimmen nicht überein.';
      return;
    }
    const payload = {
      email: this.registerData.email,
      password: this.registerData.password
    };

    this.isLoading = true;

    this.authService.register(payload).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.successMessage = 'Registrierung erfolgreich!';
        console.log('Erfolgreich registriert:', response);

        this.registerData = {
          email: '',
          password: '',
          password2: ''
        };
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Fehler:', error);

        if (error.error) {
          this.errorMessage = JSON.stringify(error.error);
        } else {
          this.errorMessage = 'Registrierung fehlgeschlagen.';
        }
      }
    });
  }

  goToLogin(event: Event): void {
    event.preventDefault();
    console.log('Zur Login-Seite');
  }
}