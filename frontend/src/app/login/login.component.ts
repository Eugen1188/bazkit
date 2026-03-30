import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';
@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  email: string = '';
  password: string = '';
  showPassword: boolean = false;

  private authService = inject(AuthService);
  private router = inject(Router);

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  onLogin(): void {
    const loginData = {
      email: this.email,
      password: this.password,
    };

    this.authService.login(loginData).subscribe({
      next: (response) => {
        console.log('Login successful', response);
        localStorage.setItem('access_token', response.access);
        localStorage.setItem('refresh_token', response.refresh);
        this.router.navigate(['/main']);
      },
      error: (error) => {
        console.error('Login failed', error);
      },
    });
  }
}
