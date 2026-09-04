import {
  Component,
  EventEmitter,
  HostListener,
  OnInit,
  Output
} from '@angular/core';

import {
  CommonModule
} from '@angular/common';
import { UiIconComponent } from '../ui-icon/ui-icon.component';

import {
  Recipe,
  RecipeIngredient,
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
    CommonModule,
    UiIconComponent
  ],

  templateUrl:
    './add-recipe-ingredients-modal.component.html',

  styleUrl:
    './add-recipe-ingredients-modal.component.scss'
})
export class AddRecipeIngredientsModalComponent
implements OnInit {

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.closeModal();
  }

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

  pendingRecipe:
    Recipe | null = null;

  includedPantryProductIds =
    new Set<number>();

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
      this.pantryIngredients(recipe).length > 0
    ) {

      this.pendingRecipe =
        recipe;

      this.includedPantryProductIds.clear();

      this.errorMessage =
        '';

      return;
    }


    this.submitRecipe(
      recipe
    );
  }


  pantryIngredients(
    recipe: Recipe | null
  ): RecipeIngredient[] {

    if (!recipe) {
      return [];
    }

    const unique =
      new Map<number, RecipeIngredient>();

    for (
      const ingredient of recipe.ingredients
    ) {

      const productId =
        ingredient.product ??
        ingredient.product_detail?.id ??
        null;

      if (
        productId !== null &&
        ingredient.product_detail?.is_common_pantry
      ) {
        unique.set(
          productId,
          ingredient
        );
      }
    }

    return Array.from(
      unique.values()
    );
  }


  pantryProductId(
    ingredient: RecipeIngredient
  ): number | null {

    return (
      ingredient.product ??
      ingredient.product_detail?.id ??
      null
    );
  }


  togglePantryIngredient(
    ingredient: RecipeIngredient
  ): void {

    const productId =
      this.pantryProductId(
        ingredient
      );

    if (productId === null) {
      return;
    }

    if (
      this.includedPantryProductIds.has(
        productId
      )
    ) {
      this.includedPantryProductIds.delete(
        productId
      );
    } else {
      this.includedPantryProductIds.add(
        productId
      );
    }
  }


  isPantryIngredientIncluded(
    ingredient: RecipeIngredient
  ): boolean {

    const productId =
      this.pantryProductId(
        ingredient
      );

    return (
      productId !== null &&
      this.includedPantryProductIds.has(
        productId
      )
    );
  }


  confirmPantrySelection(): void {

    if (!this.pendingRecipe) {
      return;
    }

    this.submitRecipe(
      this.pendingRecipe,
      Array.from(
        this.includedPantryProductIds
      )
    );
  }


  backToRecipes(): void {

    if (this.isAdding) {
      return;
    }

    this.pendingRecipe =
      null;

    this.includedPantryProductIds.clear();
  }


  private submitRecipe(
    recipe: Recipe,
    includedPantryProductIds?: number[]
  ): void {


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
        recipe.id,
        includedPantryProductIds
      )
      .subscribe({

        next: (
          shoppingList
        ) => {

          this.isAdding =
            false;

          this.selectedRecipeId =
            null;

          this.pendingRecipe =
            null;

          this.includedPantryProductIds.clear();

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
