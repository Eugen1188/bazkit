import {
  CommonModule
} from '@angular/common';

import {
  Component,
  OnDestroy,
  OnInit
} from '@angular/core';

import {
  FormsModule
} from '@angular/forms';

import {
  ActivatedRoute,
  Router
} from '@angular/router';

import {
  Subject,
  Subscription,
  debounceTime,
  distinctUntilChanged,
  switchMap
} from 'rxjs';

import {
  Recipe,
  RecipeIngredient,
  RecipeNumberValue,
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
  selector:
    'app-edit-recipe',

  standalone:
    true,

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
implements OnInit, OnDestroy {

  recipeId!: number;


  recipeName =
    '';

  description =
    '';

  servings =
    2;

  preparationTime:
    number | null =
      30;

  category =
    'dinner';

  notes =
    '';


  calories:
    number | null =
      null;

  protein:
    number | null =
      null;

  carbohydrates:
    number | null =
      null;

  fat:
    number | null =
      null;

  fiber:
    number | null =
      null;

  estimatedPrice:
    number | null =
      null;


  isSaving =
    false;

  isLoading =
    true;

  errorMessage =
    '';


  ingredients:
    RecipeIngredient[] = [];


  preparationSteps:
    PreparationStep[] = [];


  ingredientSuggestions:
    ProductSuggestion[] = [];

  activeIngredientIndex:
    number | null =
      null;

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
    private route:
      ActivatedRoute,

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
                current.index
              &&
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

            this.closeIngredientAutocompleteImmediately();
          }

        });
  }


  ngOnInit():
    void {

    this.recipeId =
      Number(
        this.route
          .snapshot
          .paramMap
          .get('id')
      );


    this.loadRecipe();
  }


  ngOnDestroy():
    void {

    this.ingredientSearchSubscription
      .unsubscribe();
  }


  loadRecipe():
    void {

    this.recipeService
      .getRecipe(
        this.recipeId
      )
      .subscribe({

        next: (
          recipe:
            Recipe
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


          this.calories =
            this.toNumberOrNull(
              recipe.calories
            );

          this.protein =
            this.toNumberOrNull(
              recipe.protein
            );

          this.carbohydrates =
            this.toNumberOrNull(
              recipe.carbohydrates
            );

          this.fat =
            this.toNumberOrNull(
              recipe.fat
            );

          this.fiber =
            this.toNumberOrNull(
              recipe.fiber
            );

          this.estimatedPrice =
            this.toNumberOrNull(
              recipe.estimated_price
            );


          this.ingredients =
            recipe.ingredients.length
              ? recipe.ingredients
                  .map(
                    ingredient => ({
                      ...ingredient
                    })
                  )
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
              )
              .filter(
                step =>
                  step.text.trim()
              );


          if (
            this.preparationSteps.length === 0
          ) {

            this.preparationSteps = [
              {
                text: ''
              }
            ];
          }


          this.isLoading =
            false;
        },


        error: (
          error
        ) => {

          console.error(
            'Rezept konnte nicht geladen werden:',
            error
          );

          this.errorMessage =
            'Rezept konnte nicht geladen werden.';

          this.isLoading =
            false;
        }

      });
  }


  private toNumberOrNull(
    value:
      RecipeNumberValue
  ): number | null {

    if (
      value === null
      ||
      value === ''
    ) {
      return null;
    }


    const numberValue =
      Number(value);


    return Number.isFinite(
      numberValue
    )
      ? numberValue
      : null;
  }


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

      this.closeIngredientAutocompleteImmediately();

      return;
    }


    this.activeIngredientIndex =
      index;

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


  closeIngredientSuggestions():
    void {

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
      product.default_unit
      &&
      this.units.includes(
        product.default_unit
      )
    ) {

      ingredient.unit =
        product.default_unit;
    }


    this.closeIngredientAutocompleteImmediately();
  }


  private closeIngredientAutocompleteImmediately():
    void {

    this.ingredientSuggestions =
      [];

    this.activeIngredientIndex =
      null;

    this.isIngredientSearching =
      false;

    this.isIngredientSuggestionsOpen =
      false;
  }


  addIngredient():
    void {

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


    this.closeIngredientAutocompleteImmediately();
  }


  canAddIngredient():
    boolean {

    if (
      this.ingredients.length === 0
    ) {
      return true;
    }


    const last =
      this.ingredients[
        this.ingredients.length - 1
      ];


    return !!last
      ?.name
      .trim();
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


    this.closeIngredientAutocompleteImmediately();
  }


  moveIngredientUp(
    index: number
  ): void {

    if (
      index <= 0
    ) {
      return;
    }


    [
      this.ingredients[index - 1],
      this.ingredients[index]
    ] = [
      this.ingredients[index],
      this.ingredients[index - 1]
    ];


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


    [
      this.ingredients[index + 1],
      this.ingredients[index]
    ] = [
      this.ingredients[index],
      this.ingredients[index + 1]
    ];


    this.closeIngredientAutocompleteImmediately();
  }


  hasIngredientContent(
    index: number
  ): boolean {

    return !!this
      .ingredients[index]
      ?.name
      .trim();
  }


  addPreparationStep():
    void {

    if (
      !this.canAddPreparationStep()
    ) {
      return;
    }


    this.preparationSteps.push({
      text: ''
    });
  }


  canAddPreparationStep():
    boolean {

    if (
      this.preparationSteps.length === 0
    ) {
      return true;
    }


    const last =
      this.preparationSteps[
        this.preparationSteps.length - 1
      ];


    return !!last
      ?.text
      .trim();
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


  hasStepContent(
    index: number
  ): boolean {

    return !!this
      .preparationSteps[index]
      ?.text
      .trim();
  }


  saveRecipe():
    void {

    this.errorMessage =
      '';


    if (
      !this.recipeName.trim()
    ) {

      this.errorMessage =
        'Bitte gib einen Rezeptnamen ein.';

      return;
    }


    if (
      !this.servings
      ||
      this.servings < 1
    ) {

      this.errorMessage =
        'Bitte gib mindestens eine Portion an.';

      return;
    }


    if (
      this.hasNegativeNutritionValue()
    ) {

      this.errorMessage =
        'Nährwerte und Preis dürfen nicht negativ sein.';

      return;
    }


    const ingredients =
      this.ingredients
        .filter(
          ingredient =>
            ingredient.name.trim()
        )
        .map(
          ingredient => ({
            id:
              ingredient.id,

            name:
              ingredient.name.trim(),

            quantity:
              ingredient.quantity,

            unit:
              ingredient.unit
          })
        );


    if (
      ingredients.length === 0
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

      calories:
        this.calories,

      protein:
        this.protein,

      carbohydrates:
        this.carbohydrates,

      fat:
        this.fat,

      fiber:
        this.fiber,

      estimated_price:
        this.estimatedPrice,

      ingredients
    };


    this.isSaving =
      true;


    this.recipeService
      .updateRecipe(
        this.recipeId,
        payload
      )
      .subscribe({

        next: () => {

          this.isSaving =
            false;


          this.router.navigate([
            '/main/recipe-list',
            this.recipeId
          ]);
        },


        error: (
          error
        ) => {

          console.error(
            'Rezept konnte nicht gespeichert werden:',
            error
          );


          this.errorMessage =
            'Rezept konnte nicht gespeichert werden.';

          this.isSaving =
            false;
        }

      });
  }


  private hasNegativeNutritionValue():
    boolean {

    const values = [
      this.calories,
      this.protein,
      this.carbohydrates,
      this.fat,
      this.fiber,
      this.estimatedPrice
    ];


    return values.some(
      value =>
        value !== null
        &&
        value < 0
    );
  }


  cancel():
    void {

    this.router.navigate([
      '/main/recipe-list',
      this.recipeId
    ]);
  }


  get ingredientCount():
    number {

    return this.ingredients
      .filter(
        ingredient =>
          ingredient.name.trim()
      )
      .length;
  }


  get stepCount():
    number {

    return this.preparationSteps
      .filter(
        step =>
          step.text.trim()
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
      ??
      'Sonstiges'
    );
  }


  get estimatedPricePerServing():
    number | null {

    if (
      this.estimatedPrice === null
      ||
      !this.servings
      ||
      this.servings <= 0
    ) {
      return null;
    }


    return (
      this.estimatedPrice
      /
      this.servings
    );
  }


  get hasNutritionData():
    boolean {

    return (
      this.calories !== null
      ||
      this.protein !== null
      ||
      this.carbohydrates !== null
      ||
      this.fat !== null
      ||
      this.fiber !== null
    );
  }
}