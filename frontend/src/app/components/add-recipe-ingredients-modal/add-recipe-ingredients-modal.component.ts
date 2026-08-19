import {
  Component,
  EventEmitter,
  OnInit,
  Output
} from '@angular/core';

import {
  CommonModule
} from '@angular/common';

import {
  Recipe,
  RecipeService
} from '../../services/recipe.service';

import {
  ShoppingList,
  ShoppingListService
} from '../../services/shopping-list.service';


@Component({
  selector:
    'app-add-recipe-ingredients-modal',

  standalone: true,

  imports: [
    CommonModule
  ],

  templateUrl:
    './add-recipe-ingredients-modal.component.html',

  styleUrl:
    './add-recipe-ingredients-modal.component.scss'
})
export class AddRecipeIngredientsModalComponent
implements OnInit {

  @Output()
  close =
    new EventEmitter<void>();


  @Output()
  shoppingListUpdated =
    new EventEmitter<ShoppingList>();


  recipes:
    Recipe[] = [];


  isLoading = true;

  isAdding = false;

  selectedRecipeId:
    number | null = null;

  errorMessage = '';


  constructor(
    private recipeService:
      RecipeService,

    private shoppingListService:
      ShoppingListService
  ) {}


  ngOnInit(): void {

    this.loadRecipes();
  }


  loadRecipes(): void {

    this.isLoading =
      true;

    this.errorMessage =
      '';


    this.recipeService
      .getRecipes()
      .subscribe({

        next: (
          recipes
        ) => {

          this.recipes =
            recipes;

          this.isLoading =
            false;
        },


        error: (
          error
        ) => {

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


  addRecipe(
    recipe: Recipe
  ): void {

    if (
      this.isAdding
    ) {
      return;
    }


    if (
      recipe.ingredients.length === 0
    ) {

      this.errorMessage =
        'Dieses Rezept enthält keine Zutaten.';

      return;
    }


    this.selectedRecipeId =
      recipe.id;

    this.isAdding =
      true;

    this.errorMessage =
      '';


    this.shoppingListService
      .addRecipe(
        recipe.id
      )
      .subscribe({

        next: (
          shoppingList
        ) => {

          this.isAdding =
            false;

          this.selectedRecipeId =
            null;

          this.shoppingListUpdated.emit(
            shoppingList
          );
        },


        error: (
          error
        ) => {

          console.error(
            'Rezept konnte nicht zur Einkaufsliste hinzugefügt werden:',
            error
          );

          this.errorMessage =
            'Die Zutaten konnten nicht übernommen werden.';

          this.isAdding =
            false;

          this.selectedRecipeId =
            null;
        }

      });
  }


  closeModal(): void {

    if (
      this.isAdding
    ) {
      return;
    }

    this.close.emit();
  }
}