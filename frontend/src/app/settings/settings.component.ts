import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

interface PreferenceItem {
  label: string;
  selected: boolean;
}

interface AccentColor {
  label: string;
  value: string;
  hex: string;
}

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss'
})
export class SettingsComponent {

  userName = 'Eugen Ferchow';

  userEmail = 'eugen@email.de';

  userInitials = 'EF';

  appVersion = 'v1.0.0';

  premiumPlanName = 'Kostenlos';

  twoFactorEnabled = false;

  appearance: 'light' | 'dark' | 'system' = 'light';

  selectedAccentColor = 'green';

  shoppingSettings = {

    defaultSorting: 'alphabetical',

    defaultUnit: 'piece',

    autoCategories: true,

    moveCompletedToBottom: true

  };

  recipeSettings = {

    defaultPortions: 2

  };

  aiSettings = {

    allowRecipeImprovement: true,

    calculateNutrition: true,

    optimizeShoppingList: false

  };

  notificationSettings = {

    shoppingReminders: true,

    sharedLists: true,

    newFeatures: true,

    newsletter: false

  };

  aiUsage = {

    used: 34,

    limit: 100

  };

  dietaryPreferences: PreferenceItem[] = [

    {
      label: 'Vegetarisch',
      selected: false
    },

    {
      label: 'Vegan',
      selected: false
    },

    {
      label: 'Glutenfrei',
      selected: false
    },

    {
      label: 'Laktosefrei',
      selected: false
    },

    {
      label: 'Low Carb',
      selected: false
    },

    {
      label: 'Proteinreich',
      selected: true
    }

  ];

  favoriteCuisines: PreferenceItem[] = [

    {
      label: 'Italienisch',
      selected: true
    },

    {
      label: 'Asiatisch',
      selected: true
    },

    {
      label: 'Deutsch',
      selected: true
    },

    {
      label: 'Mexikanisch',
      selected: false
    },

    {
      label: 'Griechisch',
      selected: false
    }

  ];

  accentColors: AccentColor[] = [

    {
      label: 'Grün',
      value: 'green',
      hex: '#587664'
    },

    {
      label: 'Blau',
      value: 'blue',
      hex: '#4d7ef7'
    },

    {
      label: 'Orange',
      value: 'orange',
      hex: '#ff9d3f'
    },

    {
      label: 'Rot',
      value: 'red',
      hex: '#df5757'
    }

  ];

  get aiUsagePercentage(): number {

    return (this.aiUsage.used / this.aiUsage.limit) * 100;

  }

  toggleDietaryPreference(item: PreferenceItem): void {

    item.selected = !item.selected;

  }

  toggleCuisine(item: PreferenceItem): void {

    item.selected = !item.selected;

  }

  selectAccentColor(color: string): void {

    this.selectedAccentColor = color;

  }

  setAppearance(value: 'light' | 'dark' | 'system'): void {

    this.appearance = value;

  }

  editProfile(): void {

    console.log('Profil bearbeiten');

  }

  changeName(): void {

    console.log('Name ändern');

  }

  changeEmail(): void {

    console.log('E-Mail ändern');

  }

  changePassword(): void {

    console.log('Passwort ändern');

  }

  addCuisine(): void {

    console.log('Neue Küche hinzufügen');

  }

  openPremium(): void {

    console.log('Premium');

  }

  openTwoFactorSettings(): void {

    console.log('2FA');

  }

  openActiveDevices(): void {

    console.log('Geräte');

  }

  downloadUserData(): void {

    console.log('Download');

  }

  deleteAccount(): void {

    console.log('Account löschen');

  }

  openPrivacyPolicy(): void {

    console.log('Datenschutz');

  }

  openTerms(): void {

    console.log('AGB');

  }

  openImprint(): void {

    console.log('Impressum');

  }

  contactSupport(): void {

    console.log('Support');

  }

}