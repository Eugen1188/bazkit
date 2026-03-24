import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from "@angular/router";

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
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
      password: this.password,
    };
  }

}
