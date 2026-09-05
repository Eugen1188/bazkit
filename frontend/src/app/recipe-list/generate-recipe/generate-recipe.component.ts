import {
  CommonModule
} from '@angular/common';

import {
  Component,
  OnInit
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
import { UserSettingsService } from '../../services/user-settings.service';
import {
  AIRecipeUsage,
  AIUsageService,
} from '../../services/ai-usage.service';

import {
  serializePreparationSteps
} from '../preparation-steps';


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
export class GenerateRecipeComponent implements OnInit {

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

  aiUsage: AIRecipeUsage | null = null;

  isUsageLoading = true;


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
      RecipeService,

    private userSettings:
      UserSettingsService,

    private aiUsageService:
      AIUsageService
  ) {
    const settings = this.userSettings.current;
    this.servings = settings.recipe_default_portions;
    this.diet = this.defaultDiet(settings.dietary_preferences);
  }


  ngOnInit(): void {
    this.aiUsageService.load().subscribe({
      next: usage => {
        this.aiUsage = usage;
        this.isUsageLoading = false;
      },
      error: () => {
        this.isUsageLoading = false;
        this.errorMessage = 'Dein KI-Kontingent konnte nicht geladen werden.';
      },
    });
  }


  get aiUsagePercentage(): number {
    if (!this.aiUsage?.limit) return 0;
    return Math.min(100, Math.round((this.aiUsage.used / this.aiUsage.limit) * 100));
  }


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
        this.category,

      dietary_preferences:
        this.userSettings.current.dietary_preferences,

      favorite_cuisines:
        this.userSettings.current.favorite_cuisines
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

          if (recipe.ai_usage) {
            this.aiUsage = recipe.ai_usage;
            this.aiUsageService.setUsage(recipe.ai_usage);
          }

          this.generatedRecipe =
            recipe;

          this.isGenerating =
            false;
        },


        error: (
          error: unknown
        ) => {

          const response = error as { error?: { ai_usage?: AIRecipeUsage } };
          if (response.error?.ai_usage) {
            this.aiUsage = response.error.ai_usage;
            this.aiUsageService.setUsage(response.error.ai_usage);
          }

          console.error(
            'KI-Rezept konnte nicht generiert werden:',
            error
          );

          this.errorMessage = this.apiError(
            error,
            'Das Rezept konnte nicht generiert werden.'
          );

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
      serializePreparationSteps(
        this.generatedRecipe.steps
      );


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

      image_position_x:
        50,

      image_position_y:
        50,

      image_zoom:
        100,

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

          this.errorMessage = this.apiError(
            error,
            'Das Rezept konnte nicht gespeichert werden.'
          );

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


  private apiError(error: unknown, fallback: string): string {
    const response = error as { error?: { detail?: string } };
    return response?.error?.detail || fallback;
  }


  private defaultDiet(preferences: string[]): string {
    const supported = ['vegan', 'vegetarian', 'high_protein', 'low_carb'];
    return supported.find(item => preferences.includes(item)) ?? 'none';
  }
}
