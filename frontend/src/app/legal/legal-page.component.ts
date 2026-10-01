import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Title } from '@angular/platform-browser';
import { ActivatedRoute, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { BrandLogoComponent } from '../components/brand-logo/brand-logo.component';


type LegalPage = 'impressum' | 'datenschutz' | 'agb';


@Component({
  selector: 'app-legal-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive, BrandLogoComponent],
  templateUrl: './legal-page.component.html',
  styleUrl: './legal-page.component.scss',
})
export class LegalPageComponent {
  page: LegalPage = 'impressum';
  readonly backTarget: string;
  readonly backLabel: string;
  contact = {
    name: '',
    email: '',
    subject: '',
    message: '',
  };
  contactSending = false;
  contactSuccess = '';
  contactError = '';

  constructor(
    route: ActivatedRoute,
    title: Title,
    private readonly authService: AuthService,
  ) {
    this.backTarget = authService.isLoggedIn() ? '/main/settings' : '/';
    this.backLabel = authService.isLoggedIn()
      ? 'Zurück zu den Einstellungen'
      : 'Zurück zur Anmeldung';

    route.data.subscribe(data => {
      this.page = data['legalPage'] as LegalPage;
      const labels: Record<LegalPage, string> = {
        impressum: 'Impressum',
        datenschutz: 'Datenschutz',
        agb: 'Nutzungsbedingungen',
      };
      title.setTitle(`${labels[this.page]} | bazkit`);
    });
  }

  sendContactMessage(): void {
    if (this.contactSending) return;
    this.contactSending = true;
    this.contactSuccess = '';
    this.contactError = '';
    this.authService.sendContactMessage(this.contact).subscribe({
      next: response => {
        this.contactSending = false;
        this.contactSuccess = response.message;
        this.contact = { name: '', email: '', subject: '', message: '' };
      },
      error: () => {
        this.contactSending = false;
        this.contactError = 'Die Nachricht konnte momentan nicht versendet werden. Bitte schreibe direkt per E-Mail.';
      },
    });
  }
}
