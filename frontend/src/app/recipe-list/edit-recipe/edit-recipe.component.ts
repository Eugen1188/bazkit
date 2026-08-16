import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
  ActivatedRoute,
  Router
} from '@angular/router';

import {
  Recipe,
  RecipeIngredient,
  RecipePayload,
  RecipeService
} from '../../services/recipe.service';

interface PreparationStep {
  text: string;
}

@Component({
  selector: 'app-edit-recipe',

  standalone: true,

  imports: [
    CommonModule,
    FormsModule
  ],

  templateUrl:
    './edit-recipe.component.html',

  styleUrl:
    './edit-recipe.component.scss'
})
export class EditRecipeComponent
implements OnInit {

  recipeId!: number;

  recipeName = '';

  description = '';

  servings = 2;

  preparationTime:
    number | null = 30;

  category = 'dinner';

  notes = '';

  isSaving = false;

  isLoading = true;

  errorMessage = '';

  ingredients:
    RecipeIngredient[] = [];

  preparationSteps:
    PreparationStep[] = [];

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
    private route: ActivatedRoute,
    private router: Router,
    private recipeService: RecipeService
  ) {}

  ngOnInit(): void {

    this.recipeId = Number(
      this.route.snapshot.paramMap.get('id')
    );

    this.loadRecipe();
  }

  loadRecipe(): void {

    this.recipeService
      .getRecipe(this.recipeId)
      .subscribe({

        next: (
          recipe: Recipe
        ) => {

          this.recipeName =
            recipe.name;

          this.description =
            recipe.description;

          this.servings =
            recipe.servings;

          this.preparationTime =
            recipe.preparation_time;

          this.category =
            recipe.category;

          this.notes =
            recipe.notes;

          this.ingredients =
            recipe.ingredients.length
              ? recipe.ingredients
              : [
                  {
                    name: '',
                    quantity: 1,
                    unit: 'Stück'
                  }
                ];

          this.preparationSteps =
            recipe.instructions
              .split('\n')
              .map(
                step => ({
                  text:
                    step.replace(
                      /^\d+\.\s*/,
                      ''
                    )
                })
              );

          this.isLoading = false;
        },

        error: () => {

          this.errorMessage =
            'Rezept konnte nicht geladen werden.';

          this.isLoading = false;
        }
      });
  }

  addIngredient(): void {

    if (!this.canAddIngredient()) {
      return;
    }

    this.ingredients.push({
      name: '',
      quantity: 1,
      unit: 'Stück'
    });
  }

  canAddIngredient(): boolean {

    const last =
      this.ingredients[
        this.ingredients.length - 1
      ];

    return !!last?.name.trim();
  }

  removeIngredient(
    index: number
  ): void {

    this.ingredients.splice(
      index,
      1
    );
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

    const last =
      this.preparationSteps[
        this.preparationSteps.length - 1
      ];

    return !!last?.text.trim();
  }

  removePreparationStep(
    index: number
  ): void {

    this.preparationSteps.splice(
      index,
      1
    );
  }

  moveIngredientUp(
    index: number
  ): void {

    if (index === 0) {
      return;
    }

    [
      this.ingredients[index - 1],
      this.ingredients[index]
    ] = [
      this.ingredients[index],
      this.ingredients[index - 1]
    ];
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

    [
      this.ingredients[index + 1],
      this.ingredients[index]
    ] = [
      this.ingredients[index],
      this.ingredients[index + 1]
    ];
  }

  moveStepUp(
    index: number
  ): void {

    if (index === 0) {
      return;
    }

    [
      this.preparationSteps[index - 1],
      this.preparationSteps[index]
    ] = [
      this.preparationSteps[index],
      this.preparationSteps[index - 1]
    ];
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

    [
      this.preparationSteps[index + 1],
      this.preparationSteps[index]
    ] = [
      this.preparationSteps[index],
      this.preparationSteps[index + 1]
    ];
  }

  hasIngredientContent(
    index: number
  ): boolean {

    return !!this
      .ingredients[index]
      ?.name
      .trim();
  }

  hasStepContent(
    index: number
  ): boolean {

    return !!this
      .preparationSteps[index]
      ?.text
      .trim();
  }

  saveRecipe(): void {

    const instructions =
      this.preparationSteps
        .filter(
          step =>
            step.text.trim()
        )
        .map(
          (
            step,
            index
          ) =>
            `${index + 1}. ${step.text}`
        )
        .join('\n');

    const payload:
      RecipePayload = {

      name:
        this.recipeName,

      description:
        this.description,

      servings:
        this.servings,

      preparation_time:
        this.preparationTime,

      category:
        this.category,

      instructions,

      notes:
        this.notes,

      ingredients:
        this.ingredients.filter(
          ingredient =>
            ingredient.name.trim()
        )
    };

    this.isSaving = true;

    this.recipeService
      .updateRecipe(
        this.recipeId,
        payload
      )
      .subscribe({

        next: () => {

          this.router.navigate([
            '/main/recipe-list',
            this.recipeId
          ]);
        },

        error: () => {

          this.errorMessage =
            'Rezept konnte nicht gespeichert werden.';

          this.isSaving = false;
        }
      });
  }

  cancel(): void {

    this.router.navigate([
      '/main/recipe-list',
      this.recipeId
    ]);
  }

  get ingredientCount(): number {

    return this.ingredients.filter(
      ingredient =>
        ingredient.name.trim()
    ).length;
  }

  get stepCount(): number {

    return this.preparationSteps.filter(
      step =>
        step.text.trim()
    ).length;
  }

  get categoryLabel(): string {

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