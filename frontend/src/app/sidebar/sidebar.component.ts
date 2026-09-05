import {
  CommonModule
} from '@angular/common';

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
import { UiIconComponent } from '../components/ui-icon/ui-icon.component';
import {
  AIRecipeUsage,
  AIUsageService,
} from '../services/ai-usage.service';


@Component({
  selector: 'app-sidebar',

  standalone: true,

  imports: [
    CommonModule,
    RouterModule,
    UiIconComponent
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

  private aiUsageService =
    inject(AIUsageService);

  aiUsage: AIRecipeUsage | null = null;


  get user() {
    return this.authService.getCurrentUser();
  }


  isMobileMoreOpen =
    false;


  constructor() {

    this.aiUsageService.load().subscribe({
      next: usage => { this.aiUsage = usage; },
      error: () => { this.aiUsage = null; },
    });

    this.router.events
      .pipe(
        filter(
          event =>
            event instanceof
            NavigationEnd
        )
      )
      .subscribe(
        () => {

          this.isMobileMoreOpen =
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


  toggleMobileMore(
    event: MouseEvent
  ): void {

    event.stopPropagation();

    this.isMobileMoreOpen =
      !this.isMobileMoreOpen;
  }


  closeMobileMore():
    void {

    this.isMobileMoreOpen =
      false;
  }


  @HostListener(
    'document:click'
  )
  onDocumentClick():
    void {

    this.isMobileMoreOpen =
      false;
  }


  logout():
    void {

    this.closeMobileMore();

    this.authService.logout();

    this.router.navigate([
      '/'
    ]);
  }

}
