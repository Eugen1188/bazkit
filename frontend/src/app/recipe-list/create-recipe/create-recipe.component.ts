import { CommonModule } from '@angular/common';
import { Component, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject, Subscription, debounceTime, distinctUntilChanged, map, of, switchMap, tap } from 'rxjs';
import { PriceEstimate, ProductService, ProductSuggestion } from '../../services/product.service';
import { RecipeIngredient, RecipePayload, RecipeService } from '../../services/recipe.service';

interface PreparationStep { text: string; }
interface IngredientSearch { index: number; query: string; }

@Component({
  selector: 'app-create-recipe',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: '../recipe-wizard/recipe-wizard.component.html',
  styleUrl: '../recipe-wizard/recipe-wizard.component.scss',
})
export class CreateRecipeComponent implements OnDestroy {
  readonly isEditMode = false;
  readonly wizardSteps = [
    { number: 1, label: 'Rezept', hint: 'Grunddaten' },
    { number: 2, label: 'Zutaten', hint: 'Produkte & Mengen' },
    { number: 3, label: 'Zubereitung', hint: 'Schritt für Schritt' },
    { number: 4, label: 'Überprüfen', hint: 'Alles auf einen Blick' },
  ];
  currentStep = 1;
  isLoading = false;
  recipeName = '';
  description = '';
  servings = 2;
  preparationTime: number | null = 30;
  category = 'dinner';
  notes = '';
  calories: number | null = null;
  protein: number | null = null;
  carbohydrates: number | null = null;
  fat: number | null = null;
  fiber: number | null = null;
  estimatedPrice: number | null = null;
  isSaving = false;
  errorMessage = '';
  imageUrl: string | null = null;
  imagePreviewUrl: string | null = null;
  selectedImageFile: File | null = null;
  isImageDragging = false;
  ingredients: RecipeIngredient[] = [this.emptyIngredient()];
  selectedProducts: Array<ProductSuggestion | null> = [null];
  preparationSteps: PreparationStep[] = [{ text: '' }];
  ingredientSuggestions: ProductSuggestion[] = [];
  activeIngredientIndex: number | null = null;
  isIngredientSearching = false;
  isIngredientSuggestionsOpen = false;
  selectingIngredientIndex: number | null = null;
  ingredientPriceLoading: boolean[] = [false];

  readonly units = ['Stück', 'g', 'kg', 'ml', 'Liter', 'EL', 'TL', 'Prise', 'Zehe', 'Scheibe', 'Tasse', 'Packung', 'Dose', 'Glas', 'Becher', 'Bund'];
  readonly categories = [
    { value: 'breakfast', label: 'Frühstück' }, { value: 'lunch', label: 'Mittagessen' },
    { value: 'dinner', label: 'Abendessen' }, { value: 'snack', label: 'Snack' },
    { value: 'dessert', label: 'Dessert' }, { value: 'other', label: 'Sonstiges' },
  ];

  private readonly search$ = new Subject<IngredientSearch>();
  private readonly searchSubscription: Subscription;
  private pendingRecipeId: number | null = null;

  constructor(
    private readonly router: Router,
    private readonly recipeService: RecipeService,
    private readonly productService: ProductService,
  ) {
    this.searchSubscription = this.search$.pipe(
      debounceTime(450),
      distinctUntilChanged((a, b) => a.index === b.index && a.query === b.query),
      switchMap(search => {
        this.activeIngredientIndex = search.index;
        this.isIngredientSearching = true;
        return this.productService.searchProducts(search.query, true).pipe(
          map(products => ({ search, products })),
        );
      }),
    ).subscribe({
      next: ({ search, products }) => {
        this.ingredientSuggestions = products;
        this.isIngredientSearching = false;
        this.isIngredientSuggestionsOpen = this.activeIngredientIndex !== null;
        this.productService.recordIngredientSearch(
          search.query,
          products.length,
          'recipe_create',
        ).subscribe();
      },
      error: () => {
        this.ingredientSuggestions = [];
        this.isIngredientSearching = false;
        this.errorMessage = 'Die Produktsuche ist momentan nicht erreichbar.';
      },
    });
  }

  ngOnDestroy(): void {
    this.searchSubscription.unsubscribe();
    this.revokeImagePreview();
  }

  get displayImageUrl(): string | null { return this.imagePreviewUrl || this.imageUrl; }

  onImageInputChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) this.selectImageFile(file);
    input.value = '';
  }

  onImageDragOver(event: DragEvent): void { event.preventDefault(); this.isImageDragging = true; }
  onImageDragLeave(event: DragEvent): void { event.preventDefault(); this.isImageDragging = false; }
  onImageDrop(event: DragEvent): void {
    event.preventDefault();
    this.isImageDragging = false;
    const file = event.dataTransfer?.files?.[0];
    if (file) this.selectImageFile(file);
  }
  removeRecipeImage(): void {
    this.selectedImageFile = null;
    this.revokeImagePreview();
    this.imageUrl = null;
  }

  onIngredientNameChange(index: number, value: string): void {
    const ingredient = this.ingredients[index];
    if (!ingredient) return;
    ingredient.name = value;
    ingredient.product = null;
    this.selectedProducts[index] = null;
    const query = value.trim();
    this.activeIngredientIndex = index;
    if (query.length < 2) { this.closeAutocomplete(); return; }
    this.isIngredientSuggestionsOpen = true;
    this.search$.next({ index, query });
  }

  openIngredientSuggestions(index: number): void {
    const query = this.ingredients[index]?.name.trim();
    if (query?.length >= 2) {
      this.activeIngredientIndex = index;
      this.isIngredientSuggestionsOpen = true;
      this.search$.next({ index, query });
    }
  }

  closeIngredientSuggestions(): void { window.setTimeout(() => this.closeAutocomplete(), 180); }

  selectIngredientSuggestion(index: number, suggestion: ProductSuggestion): void {
    if (!this.ingredients[index] || this.selectingIngredientIndex !== null) return;
    const searchQuery = this.ingredients[index].name.trim();
    const selectedRank = Math.max(1, this.ingredientSuggestions.indexOf(suggestion) + 1);
    this.selectingIngredientIndex = index;
    this.errorMessage = '';
    this.productService.persistExternalProduct(suggestion).subscribe({
      next: product => {
        const ingredient = this.ingredients[index];
        if (!ingredient || product.id === null) return;
        ingredient.product = product.id;
        ingredient.name = product.name;
        this.selectedProducts[index] = product;
        if (product.default_unit && this.units.includes(product.default_unit)) ingredient.unit = product.default_unit;
        this.selectingIngredientIndex = null;
        this.closeAutocomplete();
        this.refreshIngredientPrice(index);
        this.productService.recordIngredientSelection(
          searchQuery,
          product.id,
          selectedRank,
          'recipe_create',
        ).subscribe();
      },
      error: () => {
        this.selectingIngredientIndex = null;
        this.errorMessage = 'Das ausgewählte externe Produkt konnte nicht übernommen werden.';
      },
    });
  }

  addIngredient(): void { if (this.canAddIngredient()) { this.ingredients.push(this.emptyIngredient()); this.selectedProducts.push(null); this.ingredientPriceLoading.push(false); } }
  canAddIngredient(): boolean { return !this.ingredients.length || !!this.ingredients.at(-1)?.name.trim(); }
  hasIngredientContent(index: number): boolean { return !!this.ingredients[index]?.name.trim(); }
  removeIngredient(index: number): void { this.ingredients.splice(index, 1); this.selectedProducts.splice(index, 1); this.ingredientPriceLoading.splice(index, 1); if (!this.ingredients.length) { this.ingredients.push(this.emptyIngredient()); this.selectedProducts.push(null); this.ingredientPriceLoading.push(false); } this.recalculateEstimatedPrice(); }
  moveIngredientUp(index: number): void { if (index > 0) { [this.ingredients[index - 1], this.ingredients[index]] = [this.ingredients[index], this.ingredients[index - 1]]; [this.selectedProducts[index - 1], this.selectedProducts[index]] = [this.selectedProducts[index], this.selectedProducts[index - 1]]; } }
  moveIngredientDown(index: number): void { if (index < this.ingredients.length - 1) { [this.ingredients[index + 1], this.ingredients[index]] = [this.ingredients[index], this.ingredients[index + 1]]; [this.selectedProducts[index + 1], this.selectedProducts[index]] = [this.selectedProducts[index], this.selectedProducts[index + 1]]; } }
  refreshIngredientPrice(index: number): void {
    const product = this.selectedProducts[index];
    const ingredient = this.ingredients[index];
    if (!product || !ingredient || ingredient.quantity === null || ingredient.quantity <= 0) return;
    this.ingredientPriceLoading[index] = true;
    this.productService.estimatePrice(product, ingredient.quantity, ingredient.unit, 'consumption').subscribe({
      next: estimate => {
        this.ingredientPriceLoading[index] = false;
        this.applyPriceEstimate(ingredient, estimate);
        this.recalculateEstimatedPrice();
      },
      error: () => { this.ingredientPriceLoading[index] = false; },
    });
  }
  onIngredientAmountChange(index: number): void { this.refreshIngredientPrice(index); }
  addPreparationStep(): void { if (this.canAddPreparationStep()) this.preparationSteps.push({ text: '' }); }
  canAddPreparationStep(): boolean { return !this.preparationSteps.length || !!this.preparationSteps.at(-1)?.text.trim(); }
  hasStepContent(index: number): boolean { return !!this.preparationSteps[index]?.text.trim(); }
  removePreparationStep(index: number): void { this.preparationSteps.splice(index, 1); if (!this.preparationSteps.length) this.preparationSteps.push({ text: '' }); }
  moveStepUp(index: number): void { if (index > 0) [this.preparationSteps[index - 1], this.preparationSteps[index]] = [this.preparationSteps[index], this.preparationSteps[index - 1]]; }
  moveStepDown(index: number): void { if (index < this.preparationSteps.length - 1) [this.preparationSteps[index + 1], this.preparationSteps[index]] = [this.preparationSteps[index], this.preparationSteps[index + 1]]; }

  saveRecipe(): void {
    this.errorMessage = '';
    for (const step of [1, 2, 3]) {
      if (!this.validateWizardStep(step)) {
        this.currentStep = step;
        this.scrollWizardToTop();
        return;
      }
    }
    const ingredients = this.ingredients.filter(item => item.name.trim());
    const steps = this.preparationSteps.map(step => step.text.trim()).filter(Boolean);
    if (!this.recipeName.trim()) return this.fail('Bitte gib einen Rezeptnamen ein.');
    if (this.servings < 1) return this.fail('Bitte gib mindestens eine Portion an.');
    if (!ingredients.length) return this.fail('Bitte füge mindestens eine Zutat hinzu.');
    if (!steps.length) return this.fail('Bitte füge mindestens einen Zubereitungsschritt hinzu.');
    const payload: RecipePayload = {
      name: this.recipeName.trim(), description: this.description.trim(), servings: this.servings,
      preparation_time: this.preparationTime, category: this.category,
      instructions: steps.map((step, index) => `${index + 1}. ${step}`).join('\n'), notes: this.notes.trim(),
      ingredients: ingredients.map(item => ({
        product: item.product,
        name: item.name.trim(),
        quantity: item.quantity,
        unit: item.unit,
      })),
    };
    this.isSaving = true;
    const recipeRequest = this.pendingRecipeId
      ? this.recipeService.updateRecipe(this.pendingRecipeId, payload)
      : this.recipeService.createRecipe(payload).pipe(
          tap(recipe => { this.pendingRecipeId = recipe.id; }),
        );
    recipeRequest.pipe(
      switchMap(recipe => this.selectedImageFile
        ? this.recipeService.uploadRecipeImage(recipe.id, this.selectedImageFile)
        : of(recipe)
      ),
    ).subscribe({
      next: recipe => {
        this.isSaving = false;
        this.revokeImagePreview();
        void this.router.navigate(['/main/recipe-list', recipe.id]);
      },
      error: error => { this.isSaving = false; this.errorMessage = this.apiError(error); },
    });
  }

  cancel(): void { void this.router.navigate(['/main/recipe-list']); }
  nextStep(): void {
    if (!this.validateWizardStep(this.currentStep)) return;
    this.currentStep = Math.min(4, this.currentStep + 1);
    this.errorMessage = '';
    this.closeAutocomplete();
    this.scrollWizardToTop();
  }
  previousStep(): void {
    this.currentStep = Math.max(1, this.currentStep - 1);
    this.errorMessage = '';
    this.closeAutocomplete();
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
    this.closeAutocomplete();
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
  get ingredientCount(): number { return this.ingredients.filter(item => item.name.trim()).length; }
  get stepCount(): number { return this.preparationSteps.filter(item => item.text.trim()).length; }
  get filledIngredients(): RecipeIngredient[] { return this.ingredients.filter(item => item.name.trim()); }
  get filledPreparationSteps(): PreparationStep[] { return this.preparationSteps.filter(item => item.text.trim()); }
  get categoryLabel(): string { return this.categories.find(item => item.value === this.category)?.label ?? 'Sonstiges'; }
  get estimatedPricePerServing(): number | null {
    return this.estimatedPrice !== null && this.servings > 0 ? this.estimatedPrice / this.servings : null;
  }
  get totalPriceIngredientCount(): number {
    return this.ingredients.filter((ingredient, index) =>
      !!this.selectedProducts[index] && ingredient.product != null && ingredient.name.trim().length > 0
    ).length;
  }
  get priceIngredientCount(): number {
    return this.ingredients.filter((ingredient, index) =>
      !!this.selectedProducts[index] && ingredient.estimated_price !== null && ingredient.estimated_price !== undefined
    ).length;
  }
  get priceCoveragePercent(): number {
    return this.totalPriceIngredientCount > 0
      ? Math.round(this.priceIngredientCount / this.totalPriceIngredientCount * 100)
      : 0;
  }
  get hasSufficientPriceCoverage(): boolean {
    return this.totalPriceIngredientCount > 0 && this.priceCoveragePercent >= 70;
  }
  get priceIsComplete(): boolean {
    return this.totalPriceIngredientCount > 0 && this.priceIngredientCount === this.totalPriceIngredientCount;
  }
  nutritionValue(product: ProductSuggestion | null, field: 'calories' | 'protein' | 'carbohydrates' | 'fat' | 'fiber'): number | null {
    if (!product) return null;
    const value = product[`${field}_per_100g` as keyof ProductSuggestion];
    if (value === null || value === '') return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  nutritionPerServing(field: 'calories' | 'protein' | 'carbohydrates' | 'fat' | 'fiber'): number | null {
    let total = 0;
    let hasValue = false;
    this.ingredients.forEach((ingredient, index) => {
      const per100g = this.nutritionValue(this.selectedProducts[index], field);
      const grams = this.ingredientGrams(ingredient, this.selectedProducts[index]);
      if (per100g !== null && grams !== null) { total += per100g * grams / 100; hasValue = true; }
    });
    return hasValue && this.servings > 0 ? Math.round(total / this.servings * 100) / 100 : null;
  }
  nutritionForDisplay(field: 'calories' | 'protein' | 'carbohydrates' | 'fat' | 'fiber'): number | null {
    return this.nutritionPerServing(field);
  }
  canCalculateIngredient(index: number): boolean { return this.ingredientGrams(this.ingredients[index], this.selectedProducts[index]) !== null; }
  hasSelectedNutrition(): boolean { return this.selectedProducts.some(product => product && ['calories', 'protein', 'carbohydrates', 'fat', 'fiber'].some(field => this.nutritionValue(product, field as any) !== null)); }
  private ingredientGrams(ingredient: RecipeIngredient | undefined, product: ProductSuggestion | null): number | null {
    if (!ingredient || ingredient.quantity === null || ingredient.quantity === undefined) return null;
    const unit = ingredient.unit.trim().toLocaleLowerCase('de-DE');
    const factors: Record<string, number> = { g: 1, kg: 1000, ml: 1, liter: 1000, l: 1000 };
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
  private emptyIngredient(): RecipeIngredient { return { product: null, name: '', quantity: 1, unit: 'Stück', estimated_price: null, price_source: '', price_currency: 'EUR', price_sample_count: 0 }; }
  private applyPriceEstimate(ingredient: RecipeIngredient, estimate: PriceEstimate): void {
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
  }
  private recalculateEstimatedPrice(): void {
    const prices = this.ingredients.map(item => item.estimated_price).filter((value): value is number => value !== null && value !== undefined);
    this.estimatedPrice = prices.length && this.hasSufficientPriceCoverage
      ? Math.round(prices.reduce((sum, value) => sum + Number(value), 0) * 100) / 100
      : null;
  }
  private closeAutocomplete(): void { this.ingredientSuggestions = []; this.activeIngredientIndex = null; this.isIngredientSuggestionsOpen = false; this.isIngredientSearching = false; }
  private validateWizardStep(step: number): boolean {
    this.errorMessage = '';
    if (step === 1) {
      if (!this.recipeName.trim()) { this.fail('Gib deinem Rezept bitte einen Namen.'); return false; }
      if (!this.servings || this.servings < 1) { this.fail('Bitte gib mindestens eine Portion an.'); return false; }
    }
    if (step === 2) {
      const ingredients = this.ingredients.filter(item => item.name.trim());
      if (!ingredients.length) { this.fail('Füge bitte mindestens eine Zutat hinzu.'); return false; }
      const unselected = ingredients.find(item => item.product == null);
      if (unselected) { this.fail(`Wähle „${unselected.name.trim()}“ bitte aus den Produktvorschlägen aus.`); return false; }
      if (ingredients.some(item => item.quantity == null || Number(item.quantity) <= 0)) {
        this.fail('Bitte gib für jede Zutat eine Menge größer als null an.'); return false;
      }
    }
    if (step === 3 && !this.stepCount) { this.fail('Füge bitte mindestens einen Zubereitungsschritt hinzu.'); return false; }
    return true;
  }
  private scrollWizardToTop(): void {
    window.setTimeout(() => document.querySelector('.recipe-wizard-page')?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  }
  private selectImageFile(file: File): void {
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      this.fail('Bitte wähle ein JPG-, PNG- oder WebP-Bild aus.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      this.fail('Das Rezeptbild darf höchstens 10 MB groß sein.');
      return;
    }
    this.revokeImagePreview();
    this.selectedImageFile = file;
    this.imagePreviewUrl = URL.createObjectURL(file);
    this.errorMessage = '';
  }
  private revokeImagePreview(): void {
    if (this.imagePreviewUrl) URL.revokeObjectURL(this.imagePreviewUrl);
    this.imagePreviewUrl = null;
  }
  private fail(message: string): void { this.errorMessage = message; }
  private apiError(error: any): string { return error?.error?.image || error?.error?.ingredients?.[0] || error?.error?.detail || 'Das Rezept konnte nicht gespeichert werden.'; }
}
