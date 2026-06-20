import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
interface SidebarNavItem {
  label: string;
  route: string;
  icon: string;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterModule, CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss'
})
export class SidebarComponent {
  userName = 'Eugen';
  userEmail = 'eugen@example.com';

  navItems: SidebarNavItem[] = [
    {
      label: 'Einkaufsliste',
      route: '/main/shopping-list',
      icon: 'shopping-list'
    },
    {
      label: 'Gespeicherte Listen',
      route: '/main/saved-list',
      icon: 'saved-list'
    },
    {
      label: 'Rezepte',
      route: '/main/recipe-list',
      icon: 'recipes'
    },
    {
      label: 'Einstellungen',
      route: '/main/settings',
      icon: 'settings'
    }
  ];
}