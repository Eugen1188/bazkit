import {
  Routes
} from '@angular/router';

import {
  LoginComponent
} from './login/login.component';

import {
  RegisterComponent
} from './register/register.component';

import {
  MainComponent
} from './main/main.component';

import {
  HomeComponent
} from './home/home.component';

import {
  SavedListComponent
} from './saved-list/saved-list.component';

import {
  ShoppingListComponent
} from './shopping-list/shopping-list.component';

import {
  RecipeListComponent
} from './recipe-list/recipe-list.component';

import {
  SettingsComponent
} from './settings/settings.component';

import {
  CreateListComponent
} from './saved-list/create-list/create-list.component';

import {
  authGuard
} from './guards/auth.guard';

import {
  SavedListDetailComponent
} from './saved-list/saved-list-detail/saved-list-detail.component';

import {
  SavedListEditComponent
} from './saved-list/saved-list-edit/saved-list-edit.component';

import {
  CreateRecipeComponent
} from './recipe-list/create-recipe/create-recipe.component';

import {
  RecipeDetailComponent
} from './recipe-list/recipe-detail/recipe-detail.component';

import {
  EditRecipeComponent
} from './recipe-list/edit-recipe/edit-recipe.component';

import {
  GenerateRecipeComponent
} from './recipe-list/generate-recipe/generate-recipe.component';

import {
  CommunityComponent
} from './community/community.component';

import {
  CommunityDetailComponent
} from './community/community-detail/community-detail.component';

import {
  WeeklyPlannerComponent
} from './weekly-planner/weekly-planner.component';

import {
  LegalPageComponent
} from './legal/legal-page.component';

export const routes:
  Routes = [

    {
      path: '',
      component: LoginComponent
    },

    {
      path: 'register',
      component: RegisterComponent
    },

    {
      path: 'impressum',
      component: LegalPageComponent,
      data: { legalPage: 'impressum' }
    },

    {
      path: 'datenschutz',
      component: LegalPageComponent,
      data: { legalPage: 'datenschutz' }
    },

    {
      path: 'agb',
      component: LegalPageComponent,
      data: { legalPage: 'agb' }
    },

    {
      path: 'main',

      component:
        MainComponent,

      canActivate: [
        authGuard
      ],

      children: [

        {
          path: 'home',
          component: HomeComponent
        },

        {
          path: 'saved-list/create',
          component: CreateListComponent
        },

        {
          path: 'saved-list/:id/edit',
          component: SavedListEditComponent
        },

        {
          path: 'saved-list/:id',
          component: SavedListDetailComponent
        },

        {
          path: 'saved-list',
          component: SavedListComponent
        },

        {
          path: 'shopping-list',
          component: ShoppingListComponent
        },

        {
          path: 'recipe-list/create',
          component: CreateRecipeComponent
        },

        {
          path: 'recipe-list/ai',
          component: GenerateRecipeComponent
        },

        {
          path: 'recipe-list/:id/edit',
          component: EditRecipeComponent
        },

        {
          path: 'recipe-list/:id',
          component: RecipeDetailComponent
        },

        {
          path: 'recipe-list',
          component: RecipeListComponent
        },

        {
          path: 'community/:id',
          component: CommunityDetailComponent
        },

        {
          path: 'community',
          component: CommunityComponent
        },

        {
          path: 'settings',
          component: SettingsComponent
        },

        {
          path:
            'weekly-planner',
          component: WeeklyPlannerComponent
        },

        {
          path: '',
          redirectTo: 'home',
          pathMatch: 'full'
        }

      ]
    }

  ];
