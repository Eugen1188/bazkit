import { CommonModule } from '@angular/common';
import { Component, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject, Subscription, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';
import { PriceEstimate, ProductService, ProductSuggestion } from '../../services/product.service';
import { RecipeIngredient, RecipePayload, RecipeService } from '../../services/recipe.service';

interface PreparationStep { text: string; }
interface IngredientSearch { index: number; query: string; }

const AVERAGE_UNIT_WEIGHT_GRAMS: Record<string, number> = {
  banane: 120, apfel: 180, birne: 180, orange: 150, mandarine: 80,
  zitrone: 80, kiwi: 75, avocado: 150, tomate: 120, kartoffel: 150,
  süßkartoffel: 250, zwiebel: 100, karotte: 80, gurke: 350,
  zucchini: 200, paprika: 150, ei: 60, hähnchenbrust: 180,
};

@Component({
  selector: 'app-create-recipe',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './create-recipe.component.html',
  styleUrl: './create-recipe.component.scss',
})
export class CreateRecipeComponent implements OnDestroy {
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
  ingredients: RecipeIngredient[] = [this.emptyIngredient()];
  selectedProducts: Array<ProductSuggestion | null> = [null];
  preparationSteps: PreparationStep[] = [{ text: '' }];
  ingredientSuggestions: ProductSuggestion[] = [];
  activeIngredientIndex: number | null = null;
  isIngredientSearching = false;
  isIngredientSuggestionsOpen = false;
  selectingIngredientIndex: number | null = null;
  ingredientPriceLoading: boolean[] = [false];

  readonly units = ['Stück', 'g', 'kg', 'ml', 'Liter', 'EL', 'TL', 'Packung', 'Dose', 'Glas', 'Becher', 'Bund', 'Prise'];
  readonly categories = [
    { value: 'breakfast', label: 'Frühstück' }, { value: 'lunch', label: 'Mittagessen' },
    { value: 'dinner', label: 'Abendessen' }, { value: 'snack', label: 'Snack' },
    { value: 'dessert', label: 'Dessert' }, { value: 'other', label: 'Sonstiges' },
  ];

  private readonly search$ = new Subject<IngredientSearch>();
  private readonly searchSubscription: Subscription;

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
        return this.productService.searchProducts(search.query, true);
      }),
    ).subscribe({
      next: products => {
        this.ingredientSuggestions = products;
        this.isIngredientSearching = false;
        this.isIngredientSuggestionsOpen = this.activeIngredientIndex !== null;
      },
      error: () => {
        this.ingredientSuggestions = [];
        this.isIngredientSearching = false;
        this.errorMessage = 'Die Produktsuche ist momentan nicht erreichbar.';
      },
    });
  }

  ngOnDestroy(): void { this.searchSubscription.unsubscribe(); }

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
  addPreparationStep(): void { if (this.canAddPreparationStep()) this.preparationSteps.push({ text: '' }); }
  canAddPreparationStep(): boolean { return !this.preparationSteps.length || !!this.preparationSteps.at(-1)?.text.trim(); }
  hasStepContent(index: number): boolean { return !!this.preparationSteps[index]?.text.trim(); }
  removePreparationStep(index: number): void { this.preparationSteps.splice(index, 1); if (!this.preparationSteps.length) this.preparationSteps.push({ text: '' }); }
  moveStepUp(index: number): void { if (index > 0) [this.preparationSteps[index - 1], this.preparationSteps[index]] = [this.preparationSteps[index], this.preparationSteps[index - 1]]; }
  moveStepDown(index: number): void { if (index < this.preparationSteps.length - 1) [this.preparationSteps[index + 1], this.preparationSteps[index]] = [this.preparationSteps[index], this.preparationSteps[index + 1]]; }

  saveRecipe(): void {
    this.errorMessage = '';
    const ingredients = this.ingredients.filter(item => item.name.trim());
    const steps = this.preparationSteps.map(step => step.text.trim()).filter(Boolean);
    if (!this.recipeName.trim()) return this.fail('Bitte gib einen Rezeptnamen ein.');
    if (this.servings < 1) return this.fail('Bitte gib mindestens eine Portion an.');
    if (!ingredients.length) return this.fail('Bitte füge mindestens eine Zutat hinzu.');
    const unselected = ingredients.find(item => item.product == null);
    if (unselected) return this.fail(`Bitte wähle „${unselected.name.trim()}“ aus den Produktvorschlägen aus.`);
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
    this.recipeService.createRecipe(payload).subscribe({
      next: () => { this.isSaving = false; void this.router.navigate(['/main/recipe-list']); },
      error: error => { this.isSaving = false; this.errorMessage = this.apiError(error); },
    });
  }

  cancel(): void { void this.router.navigate(['/main/recipe-list']); }
  get ingredientCount(): number { return this.ingredients.filter(item => item.name.trim()).length; }
  get stepCount(): number { return this.preparationSteps.filter(item => item.text.trim()).length; }
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
  canCalculateIngredient(index: number): boolean { return this.ingredientGrams(this.ingredients[index], this.selectedProducts[index]) !== null; }
  hasSelectedNutrition(): boolean { return this.selectedProducts.some(product => product && ['calories', 'protein', 'carbohydrates', 'fat', 'fiber'].some(field => this.nutritionValue(product, field as any) !== null)); }
  private ingredientGrams(ingredient: RecipeIngredient | undefined, product: ProductSuggestion | null): number | null {
    if (!ingredient || ingredient.quantity === null || ingredient.quantity === undefined) return null;
    const unit = ingredient.unit.trim().toLocaleLowerCase('de-DE');
    const factors: Record<string, number> = { g: 1, kg: 1000, ml: 1, liter: 1000, l: 1000, el: 15, esslöffel: 15, tl: 5, teelöffel: 5, prise: 0.35 };
    const factor = factors[unit];
    if (factor !== undefined) return Number(ingredient.quantity) * factor;
    if (unit !== 'stück' && unit !== 'stueck') return null;
    const productName = (product?.canonical_name || product?.name || ingredient.name).trim().toLocaleLowerCase('de-DE');
    const averageWeight = AVERAGE_UNIT_WEIGHT_GRAMS[productName];
    return averageWeight === undefined ? null : Number(ingredient.quantity) * averageWeight;
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
  private fail(message: string): void { this.errorMessage = message; }
  private apiError(error: any): string { return error?.error?.ingredients?.[0] || error?.error?.detail || 'Das Rezept konnte nicht gespeichert werden.'; }
}
