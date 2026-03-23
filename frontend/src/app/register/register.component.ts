import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss'
})
export class RegisterComponent {
  username = '';
  displayName = '';
  email = '';
  password = '';
  confirmPassword = '';

  showPassword = false;
  showConfirmPassword = false;

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  toggleConfirmPassword(): void {
    this.showConfirmPassword = !this.showConfirmPassword;
  }

  onRegister(): void {
    if (this.password !== this.confirmPassword) {
      return;
    }

    console.log('Registrierung absenden', {
      username: this.username,
      display_name: this.displayName,
      email: this.email,
      password: this.password
    });
  }

  goToLogin(event: Event): void {
    event.preventDefault();
    console.log('Zur Login-Seite');
  }
}
