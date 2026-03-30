import { Routes } from '@angular/router';
import { LoginComponent } from './login/login.component';
import { RegisterComponent } from './register/register.component';
import { MainComponent } from './main/main.component';
import { SavedListComponent } from './saved-list/saved-list.component';

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
        path: '',
        redirectTo: 'saved-list',
        pathMatch: 'full',
      },
    ],
  },
];