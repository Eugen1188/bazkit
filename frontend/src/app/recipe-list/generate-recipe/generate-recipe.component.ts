import {
  CommonModule
} from '@angular/common';

import {
  Component
} from '@angular/core';

import {
  FormsModule
} from '@angular/forms';

import {
  Router
} from '@angular/router';

import {
  GeneratedRecipe,
  GenerateRecipePayload,
  RecipePayload,
  RecipeService
} from '../../services/recipe.service';
import { UiIconComponent } from '../../components/ui-icon/ui-icon.component';


@Component({
  selector: 'app-generate-recipe',

  standalone: true,

  imports: [
    CommonModule,
    FormsModule,
    UiIconComponent
  ],

  templateUrl:
    './generate-recipe.component.html',

  styleUrl:
    './generate-recipe.component.scss'
})
export class GenerateRecipeComponent {

  idea = '';

  availableIngredients = '';

  avoidIngredients = '';

  diet = 'none';

  servings = 2;

  maxTime = 30;

  category = 'dinner';


  generatedRecipe:
    GeneratedRecipe | null = null;


  isGenerating = false;

  isSaving = false;

  errorMessage = '';


  categories = [
    {
      value: 'breakfast',
      label: 'Frühstück'
    },
    {
      value: 'lunch',
      label: 'Mittagessen'
    },
    {
      value: 'dinner',
      label: 'Abendessen'
    },
    {
      value: 'snack',
      label: 'Snack'
    },
    {
      value: 'dessert',
      label: 'Dessert'
    },
    {
      value: 'other',
      label: 'Sonstiges'
    }
  ];


  diets = [
    {
      value: 'none',
      label: 'Keine Einschränkung'
    },
    {
      value: 'vegetarian',
      label: 'Vegetarisch'
    },
    {
      value: 'vegan',
      label: 'Vegan'
    },
    {
      value: 'high_protein',
      label: 'Proteinreich'
    },
    {
      value: 'low_carb',
      label: 'Low Carb'
    }
  ];


  constructor(
    private router:
      Router,

    private recipeService:
      RecipeService
  ) {}


  generateRecipe(): void {

    if (
      !this.idea.trim()
      &&
      !this.availableIngredients.trim()
    ) {

      this.errorMessage =
        'Gib eine Rezeptidee oder vorhandene Zutaten ein.';

      return;
    }


    const payload:
      GenerateRecipePayload = {

      idea:
        this.idea.trim(),

      available_ingredients:
        this.availableIngredients.trim(),

      avoid_ingredients:
        this.avoidIngredients.trim(),

      diet:
        this.diet,

      servings:
        this.servings,

      max_time:
        this.maxTime,

      category:
        this.category
    };


    this.errorMessage = '';

    this.isGenerating =
      true;


    this.recipeService
      .generateRecipe(
        payload
      )
      .subscribe({

        next: (
          recipe: GeneratedRecipe
        ) => {

          this.generatedRecipe =
            recipe;

          this.isGenerating =
            false;
        },


        error: (
          error: unknown
        ) => {

          console.error(
            'KI-Rezept konnte nicht generiert werden:',
            error
          );

          this.errorMessage =
            'Das Rezept konnte nicht generiert werden.';

          this.isGenerating =
            false;
        }

      });
  }


  regenerateRecipe(): void {

    if (
      this.isGenerating
    ) {
      return;
    }

    this.generateRecipe();
  }


  saveRecipe(): void {

    if (
      !this.generatedRecipe
      ||
      this.isSaving
    ) {
      return;
    }


    const instructions =
      this.generatedRecipe.steps
        .map(
          (
            step: string,
            index: number
          ) =>
            `${index + 1}. ${step}`
        )
        .join('\n');


    const payload:
      RecipePayload = {

      name:
        this.generatedRecipe.name,

      description:
        this.generatedRecipe.description,

      servings:
        this.generatedRecipe.servings,

      preparation_time:
        this.generatedRecipe.preparation_time,

      category:
        this.generatedRecipe.category,

      instructions,

      notes:
        this.generatedRecipe.notes,

      ingredients:
        this.generatedRecipe.ingredients
    };


    this.isSaving =
      true;

    this.errorMessage =
      '';


    this.recipeService
      .createRecipe(
        payload
      )
      .subscribe({

        next: (
          savedRecipe
        ) => {

          this.isSaving =
            false;


          this.router.navigate([
            '/main/recipe-list',
            savedRecipe.id
          ]);
        },


        error: (
          error: unknown
        ) => {

          console.error(
            'KI-Rezept konnte nicht gespeichert werden:',
            error
          );

          this.errorMessage =
            'Das Rezept konnte nicht gespeichert werden.';

          this.isSaving =
            false;
        }

      });
  }


  cancel(): void {

    this.router.navigate([
      '/main/recipe-list'
    ]);
  }


  getCategoryLabel(
    category: string
  ): string {

    return (
      this.categories.find(
        item =>
          item.value === category
      )?.label
      ?? 'Sonstiges'
    );
  }


  getDietLabel(
    diet: string
  ): string {

    return (
      this.diets.find(
        item =>
          item.value === diet
      )?.label
      ?? 'Keine Einschränkung'
    );
  }
}
