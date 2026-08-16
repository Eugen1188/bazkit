import {
  Component,
  OnInit
} from '@angular/core';

import {
  CommonModule
} from '@angular/common';

import {
  Router
} from '@angular/router';

import {
  Recipe,
  RecipeService
} from '../services/recipe.service';


@Component({
  selector: 'app-recipe-list',

  standalone: true,

  imports: [
    CommonModule
  ],

  templateUrl:
    './recipe-list.component.html',

  styleUrl:
    './recipe-list.component.scss'
})
export class RecipeListComponent
implements OnInit {

  recipes: Recipe[] = [];

  isLoading = true;

  errorMessage = '';


  constructor(
    private router: Router,

    private recipeService:
      RecipeService
  ) {}


  ngOnInit(): void {
    this.loadRecipes();
  }


  loadRecipes(): void {

    this.isLoading = true;

    this.recipeService
      .getRecipes()
      .subscribe({

        next: (recipes) => {

          this.recipes =
            recipes;

          this.isLoading =
            false;
        },

        error: (error) => {

          console.error(
            'Rezepte konnten nicht geladen werden:',
            error
          );

          this.errorMessage =
            'Die Rezepte konnten nicht geladen werden.';

          this.isLoading =
            false;
        }

      });
  }


  createRecipe(): void {

    this.router.navigate([
      '/main/recipe-list/create'
    ]);
  }


  generateWithAI(): void {

    this.router.navigate([
      '/main/recipe-list/ai'
    ]);
  }


  openRecipe(
    recipe: Recipe
  ): void {

    this.router.navigate([
      '/main/recipe-list',
      recipe.id
    ]);
  }
}