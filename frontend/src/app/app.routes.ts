import { Routes } from '@angular/router';
import { LoginComponent } from './login/login.component';
import { RegisterComponent } from './register/register.component';
import { MainComponent } from './main/main.component';
import { SavedListComponent } from './saved-list/saved-list.component';
import { ShoppingListComponent } from './shopping-list/shopping-list.component';
import { RecipeListComponent } from './recipe-list/recipe-list.component';
import { SettingsComponent } from './settings/settings.component';

export const routes: Routes = [
  {
    path: '',
    component: LoginComponent,
  },
  {
    path: 'register',
    component: RegisterComponent,
  },
  {
    path: 'main',
    component: MainComponent,
    children: [
      {
        path: 'saved-list',
        component: SavedListComponent,
      },
      {
        path: 'shopping-list',
        component: ShoppingListComponent,
      },
      {
        path: 'recipe-list',
        component: RecipeListComponent,
      },
            {
        path: 'settings',
        component: SettingsComponent,
      },
      {
        path: '',
        redirectTo: 'saved-list',
        pathMatch: 'full',
      },
    ],
  },
];
