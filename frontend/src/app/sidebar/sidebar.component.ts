import {
  Component,
  HostListener,
  inject
} from '@angular/core';

import {
  NavigationEnd,
  Router,
  RouterModule
} from '@angular/router';

import {
  filter
} from 'rxjs/operators';

import {
  AuthService
} from '../services/auth.service';


@Component({
  selector: 'app-sidebar',

  standalone: true,

  imports: [
    RouterModule
  ],

  templateUrl:
    './sidebar.component.html',

  styleUrl:
    './sidebar.component.scss'
})
export class SidebarComponent {

  private authService =
    inject(AuthService);

  private router =
    inject(Router);


  user =
    this.authService.getCurrentUser();


  isMobileMenuOpen =
    false;


  constructor() {

    /*
     * Auf dem Handy schließen wir die
     * Sidebar automatisch nach Navigation.
     */
    this.router.events
      .pipe(
        filter(
          event =>
            event instanceof NavigationEnd
        )
      )
      .subscribe(
        () => {

          this.isMobileMenuOpen =
            false;
        }
      );
  }


  get userName():
    string {

    return (
      this.user?.first_name ||
      'Benutzer'
    );
  }


  get userInitial():
    string {

    return (
      this.user
        ?.first_name
        ?.charAt(0)
        ?.toUpperCase()
      ||
      '?'
    );
  }


  toggleMobileMenu(): void {

    this.isMobileMenuOpen =
      !this.isMobileMenuOpen;
  }


  closeMobileMenu(): void {

    this.isMobileMenuOpen =
      false;
  }


  logout(): void {

    /*
     * Diese Methode sollte Access-/Refresh-Token
     * aus dem AuthService entfernen.
     */
    this.authService.logout();

    this.closeMobileMenu();

    this.router.navigate([
      '/'
    ]);
  }


  @HostListener(
    'document:keydown.escape'
  )
  onEscape(): void {

    this.closeMobileMenu();
  }
}