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
  PriceEstimate,
  ProductService,
  ProductSuggestion
} from '../../services/product.service';


interface PreparationStep {
  text: string;
}

const AVERAGE_UNIT_WEIGHT_GRAMS: Record<string, number> = {
  banane: 120, apfel: 180, birne: 180, orange: 150, mandarine: 80,
  zitrone: 80, kiwi: 75, avocado: 150, tomate: 120, kartoffel: 150,
  süßkartoffel: 250, zwiebel: 100, karotte: 80, gurke: 350,
  zucchini: 200, paprika: 150, ei: 60, hähnchenbrust: 180,
};


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
  communityPostId: number | null = null;


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

  selectedProducts: Array<ProductSuggestion | null> = [];
  ingredientPriceLoading: boolean[] = [];


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
                  search.query,
                  true
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

    const communityPost = Number(this.route.snapshot.queryParamMap.get('communityPost'));
    this.communityPostId = communityPost > 0 ? communityPost : null;

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

          this.selectedProducts = this.ingredients.map(
            ingredient => ingredient.product_detail ?? null
          );
          this.ingredientPriceLoading = this.ingredients.map(() => false);
          this.recalculateNutrition();
          this.recalculateEstimatedPrice();


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

    ingredient.product = null;
    ingredient.product_detail = null;
    this.selectedProducts[index] = null;


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


    this.productService.persistExternalProduct(product).subscribe({
      next: savedProduct => {
        if (savedProduct.id === null) return;
        ingredient.product = savedProduct.id;
        ingredient.product_detail = savedProduct;
        ingredient.name = savedProduct.name;
        this.selectedProducts[index] = savedProduct;
        if (savedProduct.default_unit && this.units.includes(savedProduct.default_unit)) {
          ingredient.unit = savedProduct.default_unit;
        }
        this.closeIngredientAutocompleteImmediately();
        this.recalculateNutrition();
        this.refreshIngredientPrice(index);
      },
      error: () => { this.errorMessage = 'Das ausgewählte Produkt konnte nicht übernommen werden.'; },
    });
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
      product: null,
      name: '',
      quantity: 1,
      unit: 'Stück'
    });
    this.selectedProducts.push(null);
    this.ingredientPriceLoading.push(false);


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
    this.selectedProducts.splice(index, 1);
    this.ingredientPriceLoading.splice(index, 1);


    if (
      this.ingredients.length === 0
    ) {

      this.ingredients.push({
        product: null,
        name: '',
        quantity: 1,
        unit: 'Stück'
      });
      this.selectedProducts.push(null);
      this.ingredientPriceLoading.push(false);
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
    [this.selectedProducts[index - 1], this.selectedProducts[index]] = [this.selectedProducts[index], this.selectedProducts[index - 1]];
    [this.ingredientPriceLoading[index - 1], this.ingredientPriceLoading[index]] = [this.ingredientPriceLoading[index], this.ingredientPriceLoading[index - 1]];


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
    [this.selectedProducts[index + 1], this.selectedProducts[index]] = [this.selectedProducts[index], this.selectedProducts[index + 1]];
    [this.ingredientPriceLoading[index + 1], this.ingredientPriceLoading[index]] = [this.ingredientPriceLoading[index], this.ingredientPriceLoading[index + 1]];


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

  onIngredientAmountChange(index: number): void {
    this.recalculateNutrition();
    this.refreshIngredientPrice(index);
  }

  refreshIngredientPrice(index: number): void {
    const product = this.selectedProducts[index];
    const ingredient = this.ingredients[index];
    if (!product || !ingredient || ingredient.quantity === null || ingredient.quantity <= 0) return;
    this.ingredientPriceLoading[index] = true;
    this.productService.estimatePrice(product, ingredient.quantity, ingredient.unit, 'consumption').subscribe({
      next: (estimate: PriceEstimate) => {
        this.ingredientPriceLoading[index] = false;
        ingredient.estimated_price = estimate.available ? Number(estimate.estimated_price) : null;
        ingredient.price_source = estimate.price_source ?? '';
        ingredient.price_currency = estimate.price_currency ?? 'EUR';
        ingredient.price_date = estimate.price_date ?? null;
        ingredient.price_store = estimate.price_store ?? '';
        ingredient.price_sample_count = estimate.price_sample_count ?? 0;
        ingredient.price_min = estimate.price_min ?? null;
        ingredient.price_max = estimate.price_max ?? null;
        ingredient.package_price = estimate.package_price ?? null;
        ingredient.package_quantity = estimate.package_quantity ?? null;
        ingredient.package_unit = estimate.package_unit ?? '';
        this.recalculateEstimatedPrice();
      },
      error: () => { this.ingredientPriceLoading[index] = false; },
    });
  }

  nutritionValue(product: ProductSuggestion | null, field: 'calories' | 'protein' | 'carbohydrates' | 'fat' | 'fiber'): number | null {
    if (!product) return null;
    const raw = product[`${field}_per_100g` as keyof ProductSuggestion];
    if (raw === null || raw === '') return null;
    const value = Number(raw);
    return Number.isFinite(value) ? value : null;
  }

  recalculateNutrition(): void {
    const fields = ['calories', 'protein', 'carbohydrates', 'fat', 'fiber'] as const;
    for (const field of fields) {
      let total = 0;
      let found = false;
      this.ingredients.forEach((ingredient, index) => {
        const per100g = this.nutritionValue(this.selectedProducts[index], field);
        const grams = this.ingredientGrams(ingredient, this.selectedProducts[index]);
        if (per100g !== null && grams !== null) {
          total += per100g * grams / 100;
          found = true;
        }
      });
      this[field] = found && this.servings > 0 ? Math.round(total / this.servings * 100) / 100 : null;
    }
  }

  private ingredientGrams(ingredient: RecipeIngredient, product: ProductSuggestion | null): number | null {
    if (ingredient.quantity === null || ingredient.quantity === undefined) return null;
    const unit = ingredient.unit.trim().toLocaleLowerCase('de-DE');
    const factors: Record<string, number> = { g: 1, kg: 1000, ml: 1, l: 1000, liter: 1000, el: 15, esslöffel: 15, tl: 5, teelöffel: 5, prise: 0.35 };
    const factor = factors[unit];
    if (factor !== undefined) return Number(ingredient.quantity) * factor;
    if (unit !== 'stück' && unit !== 'stueck') return null;
    const productName = (product?.canonical_name || product?.name || ingredient.name).trim().toLocaleLowerCase('de-DE');
    const averageWeight = AVERAGE_UNIT_WEIGHT_GRAMS[productName];
    return averageWeight === undefined ? null : Number(ingredient.quantity) * averageWeight;
  }

  private recalculateEstimatedPrice(): void {
    const prices = this.ingredients.map(item => item.estimated_price).filter((value): value is number => value !== null && value !== undefined);
    this.estimatedPrice = prices.length && this.hasSufficientPriceCoverage
      ? Math.round(prices.reduce((sum, value) => sum + Number(value), 0) * 100) / 100
      : null;
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

            product:
              ingredient.product ?? null,

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

    const unselectedIngredient = ingredients.find(ingredient => ingredient.product === null);
    if (unselectedIngredient) {
      this.errorMessage = `Bitte wähle „${unselectedIngredient.name}“ aus den Produktvorschlägen aus.`;
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


          if (this.communityPostId) {
            this.router.navigate(['/main/community', this.communityPostId]);
          } else {
            this.router.navigate(['/main/recipe-list', this.recipeId]);
          }
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
    if (this.communityPostId) {
      this.router.navigate(['/main/community', this.communityPostId]);
    } else {
      this.router.navigate(['/main/recipe-list', this.recipeId]);
    }
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


  get totalPriceIngredientCount():
    number {

    return this.ingredients.filter(
      (ingredient, index) =>
        !!this.selectedProducts[index]
        && ingredient.product != null
        && ingredient.name.trim().length > 0
    ).length;
  }


  get priceIngredientCount():
    number {

    return this.ingredients.filter(
      (ingredient, index) =>
        !!this.selectedProducts[index]
        && ingredient.estimated_price !== null
        && ingredient.estimated_price !== undefined
    ).length;
  }


  get priceCoveragePercent():
    number {

    return this.totalPriceIngredientCount > 0
      ? Math.round(this.priceIngredientCount / this.totalPriceIngredientCount * 100)
      : 0;
  }


  get hasSufficientPriceCoverage():
    boolean {

    return this.totalPriceIngredientCount > 0
      && this.priceCoveragePercent >= 70;
  }


  get priceIsComplete():
    boolean {

    return this.totalPriceIngredientCount > 0
      && this.priceIngredientCount === this.totalPriceIngredientCount;
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
