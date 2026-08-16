import { CommonModule } from '@angular/common';

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
  RecipeIngredient,
  RecipePayload,
  RecipeService
} from '../../services/recipe.service';


interface PreparationStep {
  text: string;
}


@Component({
  selector: 'app-create-recipe',

  standalone: true,

  imports: [
    CommonModule,
    FormsModule
  ],

  templateUrl:
    './create-recipe.component.html',

  styleUrl:
    './create-recipe.component.scss'
})
export class CreateRecipeComponent {

  recipeName = '';

  description = '';

  servings = 2;

  preparationTime:
    number | null = 30;

  category = 'dinner';

  notes = '';

  isSaving = false;

  errorMessage = '';


  ingredients:
    RecipeIngredient[] = [
      {
        name: '',
        quantity: 1,
        unit: 'Stück'
      }
    ];


  preparationSteps:
    PreparationStep[] = [
      {
        text: ''
      }
    ];


  units = [
    'Stück',
    'g',
    'kg',
    'ml',
    'Liter',
    'EL',
    'TL',
    'Packung',
    'Dose',
    'Glas',
    'Becher',
    'Bund',
    'Prise'
  ];


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


  constructor(
    private router: Router,
    private recipeService:
      RecipeService
  ) {}


  addIngredient(): void {

    if (
      !this.canAddIngredient()
    ) {
      return;
    }

    this.ingredients.push({
      name: '',
      quantity: 1,
      unit: 'Stück'
    });
  }


  canAddIngredient(): boolean {

    if (
      this.ingredients.length === 0
    ) {
      return true;
    }

    const lastIngredient =
      this.ingredients[
        this.ingredients.length - 1
      ];

    return (
      lastIngredient.name
        .trim()
        .length > 0
    );
  }


  hasIngredientContent(
    index: number
  ): boolean {

    const ingredient =
      this.ingredients[index];

    if (!ingredient) {
      return false;
    }

    return (
      ingredient.name
        .trim()
        .length > 0
    );
  }


  removeIngredient(
    index: number
  ): void {

    this.ingredients.splice(
      index,
      1
    );

    if (
      this.ingredients.length === 0
    ) {

      this.ingredients.push({
        name: '',
        quantity: 1,
        unit: 'Stück'
      });
    }
  }


  addPreparationStep(): void {

    if (
      !this.canAddPreparationStep()
    ) {
      return;
    }

    this.preparationSteps.push({
      text: ''
    });
  }


  canAddPreparationStep(): boolean {

    if (
      this.preparationSteps.length === 0
    ) {
      return true;
    }

    const lastStep =
      this.preparationSteps[
        this.preparationSteps.length - 1
      ];

    return (
      lastStep.text
        .trim()
        .length > 0
    );
  }


  hasStepContent(
    index: number
  ): boolean {

    const step =
      this.preparationSteps[index];

    if (!step) {
      return false;
    }

    return (
      step.text
        .trim()
        .length > 0
    );
  }


  removePreparationStep(
    index: number
  ): void {

    this.preparationSteps.splice(
      index,
      1
    );

    if (
      this.preparationSteps.length === 0
    ) {

      this.preparationSteps.push({
        text: ''
      });
    }
  }


  moveIngredientUp(
    index: number
  ): void {

    if (index <= 0) {
      return;
    }

    const current =
      this.ingredients[index];

    this.ingredients[index] =
      this.ingredients[index - 1];

    this.ingredients[index - 1] =
      current;
  }


  moveIngredientDown(
    index: number
  ): void {

    if (
      index >=
      this.ingredients.length - 1
    ) {
      return;
    }

    const current =
      this.ingredients[index];

    this.ingredients[index] =
      this.ingredients[index + 1];

    this.ingredients[index + 1] =
      current;
  }


  moveStepUp(
    index: number
  ): void {

    if (index <= 0) {
      return;
    }

    const current =
      this.preparationSteps[index];

    this.preparationSteps[index] =
      this.preparationSteps[index - 1];

    this.preparationSteps[index - 1] =
      current;
  }


  moveStepDown(
    index: number
  ): void {

    if (
      index >=
      this.preparationSteps.length - 1
    ) {
      return;
    }

    const current =
      this.preparationSteps[index];

    this.preparationSteps[index] =
      this.preparationSteps[index + 1];

    this.preparationSteps[index + 1] =
      current;
  }


  saveRecipe(): void {

    this.errorMessage = '';

    if (!this.recipeName.trim()) {

      this.errorMessage =
        'Bitte gib einen Rezeptnamen ein.';

      return;
    }


    const validIngredients =
      this.ingredients
        .filter(
          ingredient =>
            ingredient.name
              .trim()
              .length > 0
        )
        .map(
          ingredient => ({
            name:
              ingredient.name.trim(),

            quantity:
              ingredient.quantity,

            unit:
              ingredient.unit
          })
        );


    if (
      validIngredients.length === 0
    ) {

      this.errorMessage =
        'Bitte füge mindestens eine Zutat hinzu.';

      return;
    }


    const validSteps =
      this.preparationSteps
        .map(
          step =>
            step.text.trim()
        )
        .filter(
          step =>
            step.length > 0
        );


    if (
      validSteps.length === 0
    ) {

      this.errorMessage =
        'Bitte füge mindestens einen Zubereitungsschritt hinzu.';

      return;
    }


    const instructions =
      validSteps
        .map(
          (
            step,
            index
          ) =>
            `${index + 1}. ${step}`
        )
        .join('\n');


    const payload:
      RecipePayload = {

      name:
        this.recipeName.trim(),

      description:
        this.description.trim(),

      servings:
        this.servings,

      preparation_time:
        this.preparationTime,

      category:
        this.category,

      instructions,

      notes:
        this.notes.trim(),

      ingredients:
        validIngredients
    };


    this.isSaving = true;


    this.recipeService
      .createRecipe(
        payload
      )
      .subscribe({

        next: () => {

          this.isSaving =
            false;

          this.router.navigate([
            '/main/recipe-list'
          ]);

        },

        error: (
          error
        ) => {

          console.error(
            'Rezept konnte nicht gespeichert werden:',
            error
          );

          this.isSaving =
            false;

          this.errorMessage =
            'Das Rezept konnte nicht gespeichert werden.';
        }

      });
  }


  cancel(): void {

    this.router.navigate([
      '/main/recipe-list'
    ]);
  }


  get ingredientCount():
    number {

    return this.ingredients
      .filter(
        ingredient =>
          ingredient.name
            .trim()
            .length > 0
      )
      .length;
  }


  get stepCount():
    number {

    return this.preparationSteps
      .filter(
        step =>
          step.text
            .trim()
            .length > 0
      )
      .length;
  }


  get categoryLabel():
    string {

    return (
      this.categories.find(
        category =>
          category.value ===
          this.category
      )?.label
      ?? 'Sonstiges'
    );
  }
}