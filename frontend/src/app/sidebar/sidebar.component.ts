import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss'
})
export class SidebarComponent {
  userName = 'Eugen';

  navItems = [
    { label: 'Übersicht', route: '/main/overview', icon: 'home' },
    { label: 'Einkaufsliste', route: '/main/shopping-list', icon: 'list' },
    { label: 'Rezepte', route: '/main/recipe-list', icon: 'recipe' },
    { label: 'Planer', route: '/main/planner', icon: 'calendar' },
    { label: 'Gespeichert', route: '/main/saved-list', icon: 'bookmark' },
    { label: 'Profil', route: '/main/profile', icon: 'user' },
    { label: 'Einstellungen', route: '/main/settings', icon: 'settings' },
  ];
}