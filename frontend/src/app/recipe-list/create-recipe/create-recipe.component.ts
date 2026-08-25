import { CommonModule } from '@angular/common';
import { Component, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject, Subscription, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';
import { ProductService, ProductSuggestion } from '../../services/product.service';
import { RecipeIngredient, RecipePayload, RecipeService } from '../../services/recipe.service';

interface PreparationStep { text: string; }
interface IngredientSearch { index: number; query: string; }

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
        return this.productService.searchProducts(search.query);
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
      },
      error: () => {
        this.selectingIngredientIndex = null;
        this.errorMessage = 'Das ausgewählte externe Produkt konnte nicht übernommen werden.';
      },
    });
  }

  addIngredient(): void { if (this.canAddIngredient()) { this.ingredients.push(this.emptyIngredient()); this.selectedProducts.push(null); } }
  canAddIngredient(): boolean { return !this.ingredients.length || !!this.ingredients.at(-1)?.name.trim(); }
  hasIngredientContent(index: number): boolean { return !!this.ingredients[index]?.name.trim(); }
  removeIngredient(index: number): void { this.ingredients.splice(index, 1); this.selectedProducts.splice(index, 1); if (!this.ingredients.length) { this.ingredients.push(this.emptyIngredient()); this.selectedProducts.push(null); } }
  moveIngredientUp(index: number): void { if (index > 0) { [this.ingredients[index - 1], this.ingredients[index]] = [this.ingredients[index], this.ingredients[index - 1]]; [this.selectedProducts[index - 1], this.selectedProducts[index]] = [this.selectedProducts[index], this.selectedProducts[index - 1]]; } }
  moveIngredientDown(index: number): void { if (index < this.ingredients.length - 1) { [this.ingredients[index + 1], this.ingredients[index]] = [this.ingredients[index], this.ingredients[index + 1]]; [this.selectedProducts[index + 1], this.selectedProducts[index]] = [this.selectedProducts[index], this.selectedProducts[index + 1]]; } }
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
    if (this.estimatedPrice !== null && this.estimatedPrice < 0) return this.fail('Der Preis darf nicht negativ sein.');
    const payload: RecipePayload = {
      name: this.recipeName.trim(), description: this.description.trim(), servings: this.servings,
      preparation_time: this.preparationTime, category: this.category,
      instructions: steps.map((step, index) => `${index + 1}. ${step}`).join('\n'), notes: this.notes.trim(),
      estimated_price: this.estimatedPrice,
      ingredients: ingredients.map(item => ({ ...item, name: item.name.trim() })),
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
      const grams = this.ingredientGrams(ingredient);
      if (per100g !== null && grams !== null) { total += per100g * grams / 100; hasValue = true; }
    });
    return hasValue && this.servings > 0 ? Math.round(total / this.servings * 100) / 100 : null;
  }
  canCalculateIngredient(index: number): boolean { return this.ingredientGrams(this.ingredients[index]) !== null; }
  hasSelectedNutrition(): boolean { return this.selectedProducts.some(product => product && ['calories', 'protein', 'carbohydrates', 'fat', 'fiber'].some(field => this.nutritionValue(product, field as any) !== null)); }
  private ingredientGrams(ingredient: RecipeIngredient | undefined): number | null {
    if (!ingredient || ingredient.quantity === null || ingredient.quantity === undefined) return null;
    const factors: Record<string, number> = { g: 1, kg: 1000, ml: 1, liter: 1000, l: 1000 };
    const factor = factors[ingredient.unit.trim().toLocaleLowerCase('de-DE')];
    return factor === undefined ? null : ingredient.quantity * factor;
  }
  private emptyIngredient(): RecipeIngredient { return { product: null, name: '', quantity: 1, unit: 'Stück' }; }
  private closeAutocomplete(): void { this.ingredientSuggestions = []; this.activeIngredientIndex = null; this.isIngredientSuggestionsOpen = false; this.isIngredientSearching = false; }
  private fail(message: string): void { this.errorMessage = message; }
  private apiError(error: any): string { return error?.error?.ingredients?.[0] || error?.error?.detail || 'Das Rezept konnte nicht gespeichert werden.'; }
}
