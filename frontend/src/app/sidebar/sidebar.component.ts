import { Component, inject } from '@angular/core';
import { RouterModule } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss'
})
export class SidebarComponent {

  private authService = inject(AuthService);

  user = this.authService.getCurrentUser();

  get userName(): string {
    return this.user?.first_name || 'Benutzer';
  }

  get userInitial(): string {
    return this.user?.first_name?.charAt(0)?.toUpperCase() || '?';
  }
}