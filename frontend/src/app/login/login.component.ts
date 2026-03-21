import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent {
  username: string = '';
  password: string = '';
  showPassword: boolean = false;

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  onLogin(): void {
    const loginData = {
      username: this.username,
      password: this.password
    };

    console.log('Login-Daten:', loginData);

    // Hier später deinen Auth-Service aufrufen
    // Beispiel:
    // this.authService.login(loginData).subscribe(...);
  }

  goToRegister(event: Event): void {
    event.preventDefault();
    console.log('Zur Registrieren-Seite wechseln');
    // Beispiel:
    // this.router.navigate(['/register']);
  }

  forgotPassword(event: Event): void {
    event.preventDefault();
    console.log('Passwort vergessen geklickt');
    // Beispiel:
    // this.router.navigate(['/forgot-password']);
  }
}
