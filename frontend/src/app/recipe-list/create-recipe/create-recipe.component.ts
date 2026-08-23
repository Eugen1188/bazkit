import { CommonModule } from '@angular/common';
import {
  Component,
  OnDestroy
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import {
  Subject,
  Subscription,
  debounceTime,
  distinctUntilChanged,
  switchMap
} from 'rxjs';

import {
  RecipeIngredient,
  RecipePayload,
  RecipeService
} from '../../services/recipe.service';

import {
  ProductService,
  ProductSuggestion
} from '../../services/product.service';


interface PreparationStep {
  text: string;
}


interface IngredientSearch {
  index: number;
  query: string;
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
export class CreateRecipeComponent
implements OnDestroy {

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


  /* =========================
     ZUTAT AUTOCOMPLETE
  ========================= */

  ingredientSuggestions:
    ProductSuggestion[] = [];

  activeIngredientIndex:
    number | null = null;

  isIngredientSearching =
    false;

  isIngredientSuggestionsOpen =
    false;


  private ingredientSearchSubject =
    new Subject<IngredientSearch>();


  private ingredientSearchSubscription:
    Subscription;


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
    private router:
      Router,

    private recipeService:
      RecipeService,

    private productService:
      ProductService
  ) {

    this.ingredientSearchSubscription =
      this.ingredientSearchSubject
        .pipe(

          debounceTime(
            250
          ),

          distinctUntilChanged(
            (
              previous,
              current
            ) =>
              previous.index ===
                current.index &&
              previous.query ===
                current.query
          ),

          switchMap(
            search => {

              this.activeIngredientIndex =
                search.index;

              this.isIngredientSearching =
                true;

              return this.productService
                .searchProducts(
                  search.query
                );
            }
          )

        )
        .subscribe({

          next: (
            products
          ) => {

            this.ingredientSuggestions =
              products;

            this.isIngredientSearching =
              false;

            this.isIngredientSuggestionsOpen =
              (
                this.activeIngredientIndex !==
                null
              );
          },


          error: (
            error
          ) => {

            console.error(
              'Zutatensuche fehlgeschlagen:',
              error
            );

            this.ingredientSuggestions =
              [];

            this.isIngredientSearching =
              false;

            this.isIngredientSuggestionsOpen =
              false;
          }

        });
  }


  ngOnDestroy(): void {

    this.ingredientSearchSubscription
      .unsubscribe();
  }


  /* =========================
     AUTOCOMPLETE
  ========================= */

  onIngredientNameChange(
    index: number,
    value: string
  ): void {

    const ingredient =
      this.ingredients[index];


    if (!ingredient) {
      return;
    }


    ingredient.name =
      value;


    const query =
      value.trim();


    this.activeIngredientIndex =
      index;


    if (
      query.length < 2
    ) {

      this.ingredientSuggestions =
        [];

      this.isIngredientSuggestionsOpen =
        false;

      this.isIngredientSearching =
        false;

      return;
    }


    this.isIngredientSuggestionsOpen =
      true;


    this.ingredientSearchSubject.next({
      index,
      query
    });
  }


  openIngredientSuggestions(
    index: number
  ): void {

    const ingredient =
      this.ingredients[index];


    if (!ingredient) {
      return;
    }


    this.activeIngredientIndex =
      index;


    if (
      ingredient.name
        .trim()
        .length >= 2
    ) {

      this.isIngredientSuggestionsOpen =
        true;


      this.ingredientSearchSubject.next({
        index,
        query:
          ingredient.name.trim()
      });
    }
  }


  closeIngredientSuggestions(): void {

    window.setTimeout(
      () => {

        this.isIngredientSuggestionsOpen =
          false;

        this.activeIngredientIndex =
          null;
      },
      180
    );
  }


  selectIngredientSuggestion(
    index: number,
    product:
      ProductSuggestion
  ): void {

    const ingredient =
      this.ingredients[index];


    if (!ingredient) {
      return;
    }


    ingredient.name =
      product.name;


    if (
      product.default_unit &&
      this.units.includes(
        product.default_unit
      )
    ) {

      ingredient.unit =
        product.default_unit;
    }


    this.ingredientSuggestions =
      [];

    this.isIngredientSuggestionsOpen =
      false;

    this.activeIngredientIndex =
      null;

    this.isIngredientSearching =
      false;
  }


  /* =========================
     INGREDIENTS
  ========================= */

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


    this.ingredientSuggestions =
      [];

    this.isIngredientSuggestionsOpen =
      false;

    this.activeIngredientIndex =
      null;
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


    this.ingredientSuggestions =
      [];

    this.isIngredientSuggestionsOpen =
      false;

    this.activeIngredientIndex =
      null;


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


  moveIngredientUp(
    index: number
  ): void {

    if (
      index <= 0
    ) {
      return;
    }


    const current =
      this.ingredients[index];


    this.ingredients[index] =
      this.ingredients[
        index - 1
      ];


    this.ingredients[
      index - 1
    ] =
      current;


    this.closeIngredientAutocompleteImmediately();
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
      this.ingredients[
        index + 1
      ];


    this.ingredients[
      index + 1
    ] =
      current;


    this.closeIngredientAutocompleteImmediately();
  }


  private closeIngredientAutocompleteImmediately():
    void {

    this.ingredientSuggestions =
      [];

    this.activeIngredientIndex =
      null;

    this.isIngredientSuggestionsOpen =
      false;

    this.isIngredientSearching =
      false;
  }


  /* =========================
     PREPARATION
  ========================= */

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


  moveStepUp(
    index: number
  ): void {

    if (
      index <= 0
    ) {
      return;
    }


    const current =
      this.preparationSteps[index];


    this.preparationSteps[index] =
      this.preparationSteps[
        index - 1
      ];


    this.preparationSteps[
      index - 1
    ] =
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
      this.preparationSteps[
        index + 1
      ];


    this.preparationSteps[
      index + 1
    ] =
      current;
  }


  /* =========================
     SAVE
  ========================= */

  saveRecipe(): void {

    this.errorMessage =
      '';


    if (
      !this.recipeName.trim()
    ) {

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


    this.isSaving =
      true;


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


  /* =========================
     GETTERS
  ========================= */

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