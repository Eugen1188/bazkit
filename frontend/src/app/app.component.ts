import { Component, OnInit } from '@angular/core';
import { RouterModule } from "@angular/router";
import { AuthService } from './services/auth.service';
import { UserSettingsService } from './services/user-settings.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  title = 'frontend';

  constructor(
    private readonly authService: AuthService,
    private readonly userSettings: UserSettingsService,
  ) {}

  ngOnInit(): void {
    if (this.authService.isLoggedIn()) {
      this.userSettings.load().subscribe({
        error: () => {
          // Die lokal gespeicherte Darstellung bleibt als verlässlicher Fallback aktiv.
        },
      });
    }
  }
}
