import { CommonModule } from '@angular/common';
import { Component, HostListener, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { BrandLogoComponent } from '../components/brand-logo/brand-logo.component';
import { UiDialogDirective } from '../components/ui-primitives/ui-primitives.directive';
import { AuthService } from '../services/auth.service';

interface LandingGate {
  title: string;
  description: string;
  returnUrl: string;
}

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    BrandLogoComponent,
    UiDialogDirective,
  ],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss',
})
export class LandingComponent {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly isLoggedIn = this.authService.isLoggedIn();
  readonly currentYear = new Date().getFullYear();

  activeGate: LandingGate | null = null;

  openFeature(
    title: string,
    description: string,
    returnUrl: string,
  ): void {
    if (this.isLoggedIn) {
      void this.router.navigateByUrl(returnUrl);
      return;
    }

    this.activeGate = { title, description, returnUrl };
  }

  closeGate(): void {
    this.activeGate = null;
  }

  scrollToFeatures(): void {
    document.getElementById('funktionen')?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    });
  }

  @HostListener('document:keydown.escape')
  closeGateWithEscape(): void {
    this.closeGate();
  }
}
