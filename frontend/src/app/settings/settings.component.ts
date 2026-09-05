import { CommonModule } from '@angular/common';
import { Component, HostListener, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  EMPTY,
  Subject,
  Subscription,
  catchError,
  concatMap,
  debounceTime,
  finalize,
  forkJoin,
} from 'rxjs';
import {
  AuthService,
  ChangePasswordPayload,
  UserProfile,
} from '../services/auth.service';
import {
  AccentColor,
  AppearanceMode,
  DEFAULT_USER_SETTINGS,
  UserSettings,
  UserSettingsService,
} from '../services/user-settings.service';
import { UiIconComponent } from '../components/ui-icon/ui-icon.component';


interface PreferenceOption {
  label: string;
  value: string;
}


interface AccentOption {
  label: string;
  value: AccentColor;
  hex: string;
}


type SettingsDialog = 'profile' | 'password' | 'delete' | null;
type SaveState = 'idle' | 'saving' | 'saved' | 'error';


@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, UiIconComponent],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss',
})
export class SettingsComponent implements OnInit, OnDestroy {
  profile: UserProfile | null = null;
  settings = this.cloneSettings(DEFAULT_USER_SETTINGS);

  isLoading = true;
  isDialogSaving = false;
  loadError = '';
  dialogError = '';
  pageMessage = '';
  saveState: SaveState = 'idle';
  activeDialog: SettingsDialog = null;

  profileForm = {
    first_name: '',
    last_name: '',
    email: '',
  };

  passwordForm: ChangePasswordPayload = {
    current_password: '',
    new_password: '',
    new_password2: '',
  };

  deleteConfirmation = '';

  readonly dietaryOptions: PreferenceOption[] = [
    { value: 'vegetarian', label: 'Vegetarisch' },
    { value: 'vegan', label: 'Vegan' },
    { value: 'gluten_free', label: 'Glutenfrei' },
    { value: 'lactose_free', label: 'Laktosefrei' },
    { value: 'low_carb', label: 'Low Carb' },
    { value: 'high_protein', label: 'Proteinreich' },
  ];

  readonly cuisineOptions: PreferenceOption[] = [
    { value: 'italian', label: 'Italienisch' },
    { value: 'asian', label: 'Asiatisch' },
    { value: 'german', label: 'Deutsch' },
    { value: 'mexican', label: 'Mexikanisch' },
    { value: 'greek', label: 'Griechisch' },
    { value: 'mediterranean', label: 'Mediterran' },
    { value: 'indian', label: 'Indisch' },
  ];

  readonly accentColors: AccentOption[] = [
    { label: 'Grün', value: 'green', hex: '#587664' },
    { label: 'Blau', value: 'blue', hex: '#4f7197' },
    { label: 'Orange', value: 'orange', hex: '#a9672f' },
    { label: 'Rot', value: 'red', hex: '#a95656' },
  ];

  private readonly saveSettings$ = new Subject<void>();
  private readonly subscriptions = new Subscription();
  private savedStateTimer: number | null = null;

  constructor(
    private readonly authService: AuthService,
    private readonly userSettings: UserSettingsService,
    private readonly router: Router,
  ) {
    this.subscriptions.add(
      this.saveSettings$.pipe(
        debounceTime(450),
        concatMap(() => {
          const snapshot = this.cloneSettings(this.settings);
          this.saveState = 'saving';

          return this.userSettings.save(snapshot).pipe(
            catchError(error => {
              this.saveState = 'error';
              this.pageMessage = this.apiError(
                error,
                'Die Einstellungen konnten nicht gespeichert werden.'
              );
              return EMPTY;
            }),
            finalize(() => {
              if (this.saveState === 'saving') {
                this.saveState = 'saved';
                this.showSavedStateTemporarily();
              }
            })
          );
        })
      ).subscribe(settings => {
        this.settings = this.cloneSettings(settings);
        this.pageMessage = '';
      })
    );
  }

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    if (this.savedStateTimer !== null) window.clearTimeout(this.savedStateTimer);
  }

  @HostListener('document:keydown.escape')
  closeDialogWithEscape(): void {
    this.closeDialog();
  }

  get userName(): string {
    if (!this.profile) return 'Benutzerkonto';
    return `${this.profile.first_name} ${this.profile.last_name}`.trim()
      || this.profile.email;
  }

  get userInitials(): string {
    const initials = [this.profile?.first_name, this.profile?.last_name]
      .filter(Boolean)
      .map(value => value?.charAt(0).toUpperCase())
      .join('');
    return initials || this.profile?.email.charAt(0).toUpperCase() || '?';
  }

  loadData(): void {
    this.isLoading = true;
    this.loadError = '';

    this.subscriptions.add(
      forkJoin({
        profile: this.authService.getMe(),
        settings: this.userSettings.load(),
      }).subscribe({
        next: ({ profile, settings }) => {
          this.profile = profile;
          this.settings = this.cloneSettings(settings);
          this.authService.storeCurrentUser(profile);
          this.isLoading = false;
        },
        error: error => {
          this.loadError = this.apiError(
            error,
            'Deine Einstellungen konnten nicht geladen werden.'
          );
          this.isLoading = false;
        },
      })
    );
  }

  settingsChanged(): void {
    this.pageMessage = '';
    this.saveState = 'idle';
    this.userSettings.preview(this.settings);
    this.saveSettings$.next();
  }

  setAppearance(value: AppearanceMode): void {
    this.settings.appearance = value;
    this.settingsChanged();
  }

  selectAccentColor(value: AccentColor): void {
    this.settings.accent_color = value;
    this.settingsChanged();
  }

  togglePreference(
    field: 'dietary_preferences' | 'favorite_cuisines',
    value: string
  ): void {
    const selected = this.settings[field];
    this.settings[field] = selected.includes(value)
      ? selected.filter(item => item !== value)
      : [...selected, value];
    this.settingsChanged();
  }

  isPreferenceSelected(
    field: 'dietary_preferences' | 'favorite_cuisines',
    value: string
  ): boolean {
    return this.settings[field].includes(value);
  }

  openProfileDialog(): void {
    if (!this.profile) return;
    this.profileForm = {
      first_name: this.profile.first_name,
      last_name: this.profile.last_name,
      email: this.profile.email,
    };
    this.openDialog('profile');
  }

  openPasswordDialog(): void {
    this.passwordForm = {
      current_password: '',
      new_password: '',
      new_password2: '',
    };
    this.openDialog('password');
  }

  openDeleteDialog(): void {
    this.deleteConfirmation = '';
    this.openDialog('delete');
  }

  closeDialog(): void {
    if (this.isDialogSaving) return;
    this.activeDialog = null;
    this.dialogError = '';
  }

  saveProfile(): void {
    if (this.isDialogSaving) return;

    const data = {
      first_name: this.profileForm.first_name.trim(),
      last_name: this.profileForm.last_name.trim(),
      email: this.profileForm.email.trim().toLowerCase(),
    };
    if (!data.first_name || !data.last_name || !data.email) {
      this.dialogError = 'Bitte fülle alle Felder aus.';
      return;
    }

    this.isDialogSaving = true;
    this.dialogError = '';
    this.authService.updateProfile(data).subscribe({
      next: profile => {
        this.profile = profile;
        this.authService.storeCurrentUser(profile);
        this.isDialogSaving = false;
        this.activeDialog = null;
        this.pageMessage = 'Dein Profil wurde aktualisiert.';
      },
      error: error => {
        this.dialogError = this.apiError(
          error,
          'Das Profil konnte nicht gespeichert werden.'
        );
        this.isDialogSaving = false;
      },
    });
  }

  submitPasswordChange(): void {
    if (this.isDialogSaving) return;
    if (this.passwordForm.new_password !== this.passwordForm.new_password2) {
      this.dialogError = 'Die neuen Passwörter stimmen nicht überein.';
      return;
    }

    this.isDialogSaving = true;
    this.dialogError = '';
    this.authService.changePassword(this.passwordForm).subscribe({
      next: () => {
        this.isDialogSaving = false;
        this.activeDialog = null;
        this.pageMessage = 'Dein Passwort wurde geändert.';
      },
      error: error => {
        this.dialogError = this.apiError(
          error,
          'Das Passwort konnte nicht geändert werden.'
        );
        this.isDialogSaving = false;
      },
    });
  }

  downloadProfileData(): void {
    if (!this.profile) return;

    const content = JSON.stringify({
      exported_at: new Date().toISOString(),
      profile: this.profile,
      settings: this.settings,
    }, null, 2);
    const url = URL.createObjectURL(new Blob([content], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `bazkit-profil-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(url);
    this.pageMessage = 'Deine Profil- und Einstellungsdaten wurden heruntergeladen.';
  }

  deleteAccount(): void {
    if (this.deleteConfirmation !== 'LÖSCHEN' || this.isDialogSaving) return;

    this.isDialogSaving = true;
    this.dialogError = '';
    this.authService.deleteAccount().subscribe({
      next: () => {
        this.userSettings.clearCache();
        this.authService.logout();
        void this.router.navigate(['/']);
      },
      error: error => {
        this.dialogError = this.apiError(
          error,
          'Das Konto konnte nicht gelöscht werden.'
        );
        this.isDialogSaving = false;
      },
    });
  }

  private openDialog(dialog: Exclude<SettingsDialog, null>): void {
    this.dialogError = '';
    this.activeDialog = dialog;
  }

  private cloneSettings(settings: UserSettings): UserSettings {
    return {
      ...settings,
      dietary_preferences: [...settings.dietary_preferences],
      favorite_cuisines: [...settings.favorite_cuisines],
    };
  }

  private showSavedStateTemporarily(): void {
    if (this.savedStateTimer !== null) window.clearTimeout(this.savedStateTimer);
    this.savedStateTimer = window.setTimeout(() => {
      if (this.saveState === 'saved') this.saveState = 'idle';
    }, 2200);
  }

  private apiError(error: unknown, fallback: string): string {
    const response = error as { error?: unknown };
    const detail = response?.error;
    if (typeof detail === 'string') return detail;
    if (detail && typeof detail === 'object') {
      const firstValue = Object.values(detail as Record<string, unknown>)[0];
      if (Array.isArray(firstValue) && firstValue.length) return String(firstValue[0]);
      if (typeof firstValue === 'string') return firstValue;
    }
    return fallback;
  }
}
