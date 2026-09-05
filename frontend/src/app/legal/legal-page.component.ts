import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { ActivatedRoute, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../services/auth.service';


type LegalPage = 'impressum' | 'datenschutz' | 'agb';


@Component({
  selector: 'app-legal-page',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './legal-page.component.html',
  styleUrl: './legal-page.component.scss',
})
export class LegalPageComponent {
  page: LegalPage = 'impressum';
  readonly backTarget: string;
  readonly backLabel: string;

  constructor(route: ActivatedRoute, title: Title, authService: AuthService) {
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
}
