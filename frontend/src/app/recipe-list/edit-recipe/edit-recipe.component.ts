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
  map,
  of,
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
    '../recipe-wizard/recipe-wizard.component.html',

  styleUrl:
    '../recipe-wizard/recipe-wizard.component.scss'
})
export class EditRecipeComponent
implements OnInit, OnDestroy {

  readonly isEditMode = true;
  readonly wizardSteps = [
    { number: 1, label: 'Rezept', hint: 'Grunddaten' },
    { number: 2, label: 'Zutaten', hint: 'Produkte & Mengen' },
    { number: 3, label: 'Zubereitung', hint: 'Schritt für Schritt' },
    { number: 4, label: 'Überprüfen', hint: 'Alles auf einen Blick' },
  ];
  currentStep = 1;

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

  isSaving =
    false;

  isLoading =
    true;

  errorMessage =
    '';

  imageUrl: string | null = null;
  imagePreviewUrl: string | null = null;
  selectedImageFile: File | null = null;
  isImageDragging = false;
  imageRemoved = false;


  ingredients:
    RecipeIngredient[] = [];

  selectedProducts: Array<ProductSuggestion | null> = [];


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
    'Stange',
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
    'Prise',
    'Zehe',
    'Scheibe',
    'Tasse'
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
                )
                .pipe(
                  map(products => ({ search, products }))
                );
            }
          )

        )
        .subscribe({

          next: (
            result
          ) => {

            this.ingredientSuggestions =
              result.products;

            this.isIngredientSearching =
              false;

            this.isIngredientSuggestionsOpen =
              (
                this.activeIngredientIndex !==
                null
              );

            this.productService.recordIngredientSearch(
              result.search.query,
              result.products.length,
              'recipe_edit'
            ).subscribe();
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

    this.revokeImagePreview();
  }


  get displayImageUrl(): string | null {
    return this.imagePreviewUrl || (this.imageRemoved ? null : this.imageUrl);
  }


  onImageInputChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) this.selectImageFile(file);
    input.value = '';
  }


  onImageDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isImageDragging = true;
  }


  onImageDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isImageDragging = false;
  }


  onImageDrop(event: DragEvent): void {
    event.preventDefault();
    this.isImageDragging = false;
    const file = event.dataTransfer?.files?.[0];
    if (file) this.selectImageFile(file);
  }


  removeRecipeImage(): void {
    if (this.selectedImageFile) {
      this.selectedImageFile = null;
      this.revokeImagePreview();
      return;
    }
    this.imageRemoved = true;
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

          this.imageUrl = recipe.image_url;
          this.imageRemoved = false;


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
          this.recalculateNutrition();


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

    const searchQuery = ingredient.name.trim();
    const selectedRank = Math.max(1, this.ingredientSuggestions.indexOf(product) + 1);


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
        this.productService.recordIngredientSelection(
          searchQuery,
          savedProduct.id,
          selectedRank,
          'recipe_edit'
        ).subscribe();
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

  canCalculateIngredient(index: number): boolean {
    const ingredient = this.ingredients[index];
    return !!ingredient && this.ingredientGrams(ingredient, this.selectedProducts[index]) !== null;
  }

  availableUnitsFor(index: number): string[] {
    const productUnits = this.selectedProducts[index]?.available_units;
    if (!productUnits?.length) return this.selectedProducts[index] ? ['g', 'kg'] : this.units;
    return productUnits.filter(unit => this.units.includes(unit));
  }

  private ingredientGrams(ingredient: RecipeIngredient, product: ProductSuggestion | null): number | null {
    if (ingredient.quantity === null || ingredient.quantity === undefined) return null;
    const unit = ingredient.unit.trim().toLocaleLowerCase('de-DE');
    const factors: Record<string, number> = { g: 1, kg: 1000, ml: 1, l: 1000, liter: 1000 };
    const factor = factors[unit];
    if (factor !== undefined) return Number(ingredient.quantity) * factor;
    const conversion = product?.unit_conversions?.find(item =>
      item.unit.trim().toLocaleLowerCase('de-DE') === unit
    );
    const averageWeight = conversion?.grams_per_unit == null ? null : Number(conversion.grams_per_unit);
    return averageWeight !== null && Number.isFinite(averageWeight) && averageWeight > 0
      ? Number(ingredient.quantity) * averageWeight
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

    for (const step of [1, 2, 3]) {
      if (!this.validateWizardStep(step)) {
        this.currentStep = step;
        this.scrollWizardToTop();
        return;
      }
    }


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
        'Nährwerte dürfen nicht negativ sein.';

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
      .pipe(
        switchMap(recipe => {
          if (this.selectedImageFile) {
            return this.recipeService.uploadRecipeImage(recipe.id, this.selectedImageFile);
          }
          if (this.imageRemoved && this.imageUrl) {
            return this.recipeService.deleteRecipeImage(recipe.id).pipe(
              map(() => ({ ...recipe, image_url: null }))
            );
          }
          return of(recipe);
        })
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
            error?.error?.image
            || error?.error?.detail
            || 'Rezept konnte nicht gespeichert werden.';

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
      this.fiber
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

  nextStep(): void {
    if (!this.validateWizardStep(this.currentStep)) return;
    this.currentStep = Math.min(4, this.currentStep + 1);
    this.errorMessage = '';
    this.closeIngredientAutocompleteImmediately();
    this.scrollWizardToTop();
  }

  previousStep(): void {
    this.currentStep = Math.max(1, this.currentStep - 1);
    this.errorMessage = '';
    this.closeIngredientAutocompleteImmediately();
    this.scrollWizardToTop();
  }

  goToStep(targetStep: number): void {
    if (targetStep < 1 || targetStep > 4 || targetStep === this.currentStep) return;
    if (targetStep > this.currentStep) {
      for (let step = this.currentStep; step < targetStep; step += 1) {
        if (!this.validateWizardStep(step)) {
          this.currentStep = step;
          this.scrollWizardToTop();
          return;
        }
      }
    }
    this.currentStep = targetStep;
    this.errorMessage = '';
    this.closeIngredientAutocompleteImmediately();
    this.scrollWizardToTop();
  }

  isStepComplete(step: number): boolean {
    if (step === 1) return !!this.recipeName.trim() && this.servings >= 1;
    if (step === 2) {
      const ingredients = this.ingredients.filter(item => item.name.trim());
      return ingredients.length > 0 && ingredients.every(item =>
        item.quantity != null && Number(item.quantity) > 0
      );
    }
    if (step === 3) return this.stepCount > 0;
    return this.isStepComplete(1) && this.isStepComplete(2) && this.isStepComplete(3);
  }

  nutritionForDisplay(field: 'calories' | 'protein' | 'carbohydrates' | 'fat' | 'fiber'): number | null {
    return this[field];
  }

  private validateWizardStep(step: number): boolean {
    this.errorMessage = '';
    if (step === 1) {
      if (!this.recipeName.trim()) {
        this.errorMessage = 'Gib deinem Rezept bitte einen Namen.';
        return false;
      }
      if (!this.servings || this.servings < 1) {
        this.errorMessage = 'Bitte gib mindestens eine Portion an.';
        return false;
      }
    }
    if (step === 2) {
      const ingredients = this.ingredients.filter(item => item.name.trim());
      if (!ingredients.length) {
        this.errorMessage = 'Füge bitte mindestens eine Zutat hinzu.';
        return false;
      }
      const unselected = ingredients.find(item => item.product == null);
      if (unselected) {
        this.errorMessage = `Wähle „${unselected.name.trim()}“ bitte aus den Produktvorschlägen aus.`;
        return false;
      }
      if (ingredients.some(item => item.quantity == null || Number(item.quantity) <= 0)) {
        this.errorMessage = 'Bitte gib für jede Zutat eine Menge größer als null an.';
        return false;
      }
    }
    if (step === 3 && !this.stepCount) {
      this.errorMessage = 'Füge bitte mindestens einen Zubereitungsschritt hinzu.';
      return false;
    }
    return true;
  }

  private scrollWizardToTop(): void {
    window.setTimeout(() => document.querySelector('.recipe-wizard-page')?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  }

  private selectImageFile(file: File): void {
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      this.errorMessage = 'Bitte wähle ein JPG-, PNG- oder WebP-Bild aus.';
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      this.errorMessage = 'Das Rezeptbild darf höchstens 10 MB groß sein.';
      return;
    }
    this.revokeImagePreview();
    this.selectedImageFile = file;
    this.imagePreviewUrl = URL.createObjectURL(file);
    this.imageRemoved = false;
    this.errorMessage = '';
  }

  private revokeImagePreview(): void {
    if (this.imagePreviewUrl) URL.revokeObjectURL(this.imagePreviewUrl);
    this.imagePreviewUrl = null;
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


  get filledIngredients() {

    return this.ingredients
      .filter(
        ingredient =>
          ingredient.name.trim()
      );
  }


  get filledPreparationSteps() {

    return this.preparationSteps
      .filter(
        step =>
          step.text.trim()
      );
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
