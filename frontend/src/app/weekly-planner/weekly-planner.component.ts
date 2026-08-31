import { CommonModule } from '@angular/common';
import { Component, HostListener, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize, forkJoin } from 'rxjs';

import { RecipeIngredient, RecipeService, RecipeSummary } from '../services/recipe.service';
import {
  PlannerMealType,
  WeeklyPlanEntry,
  WeeklyPlannerService
} from '../services/weekly-planner.service';


type MealType = PlannerMealType;
type FeedbackKind = 'success' | 'error' | '';

interface Meal {
  entryId: number;
  recipeId: number;
  name: string;
  image: string;
  imagePosition: string;
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  servings: number;
  ingredientCount: number;
}

interface PlannerDay {
  fullName: string;
  shortName: string;
  date: string;
  dateKey: string;
  dayNumber: number;
  isToday: boolean;
  breakfast: Meal[];
  lunch: Meal[];
  dinner: Meal[];
}


@Component({
  selector: 'app-weekly-planner',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './weekly-planner.component.html',
  styleUrl: './weekly-planner.component.scss'
})
export class WeeklyPlannerComponent implements OnInit {
  readonly mealTypes: { key: MealType; label: string }[] = [
    { key: 'breakfast', label: 'Frühstück' },
    { key: 'lunch', label: 'Mittagessen' },
    { key: 'dinner', label: 'Abendessen' }
  ];

  days: PlannerDay[] = [];
  recipes: RecipeSummary[] = [];
  selectedDayIndex = 0;
  weekStart = this.startOfWeek(new Date());

  isLoading = true;
  isSaving = false;
  isGenerating = false;
  isCreatingShoppingList = false;
  isLoadingRecipeDetails = false;
  aiPlannerDialogOpen = false;
  planBreakfast = true;
  planLunch = true;
  planDinner = true;
  aiDailyCalorieTarget: number | null = null;
  aiDailyProteinTarget: number | null = null;
  aiMaxRecipeRepeats = 2;
  aiServings = 2;
  aiOverwrite = false;
  pantryDialogOpen = false;
  includedPantryProductIds = new Set<number>();
  feedbackMessage = '';
  feedbackKind: FeedbackKind = '';

  mealDialogOpen = false;
  dialogDayIndex = 0;
  dialogMealType: MealType = 'dinner';
  selectedRecipeId: number | null = null;
  selectedServings = 1;
  recipeSearch = '';
  dialogEntry: Meal | null = null;

  constructor(
    private readonly router: Router,
    private readonly recipeService: RecipeService,
    private readonly plannerService: WeeklyPlannerService
  ) {}

  ngOnInit(): void {
    this.buildDays();
    this.loadInitialData();
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.aiPlannerDialogOpen) {
      this.closeAiPlannerDialog();
      return;
    }
    if (this.pantryDialogOpen) {
      this.closePantryDialog();
      return;
    }
    this.closeMealDialog();
  }

  get weekLabel(): string {
    const end = this.addDays(this.weekStart, 6);
    const startDay = this.weekStart.getDate();
    const endDay = end.getDate();
    const startMonth = this.monthName(this.weekStart);
    const endMonth = this.monthName(end);
    const startYear = this.weekStart.getFullYear();
    const endYear = end.getFullYear();

    if (startYear !== endYear) {
      return `${startDay}. ${startMonth} ${startYear} – ${endDay}. ${endMonth} ${endYear}`;
    }
    if (startMonth !== endMonth) {
      return `${startDay}. ${startMonth} – ${endDay}. ${endMonth} ${endYear}`;
    }
    return `${startDay}. – ${endDay}. ${endMonth} ${endYear}`;
  }

  get selectedDay(): PlannerDay {
    return this.days[this.selectedDayIndex] ?? this.days[0];
  }

  get dialogDay(): PlannerDay | null {
    return this.days[this.dialogDayIndex] ?? null;
  }

  get dialogMealLabel(): string {
    return this.mealTypes.find(item => item.key === this.dialogMealType)?.label ?? 'Mahlzeit';
  }

  get selectedRecipe(): RecipeSummary | null {
    return this.recipes.find(recipe => recipe.id === this.selectedRecipeId) ?? null;
  }

  get filteredRecipes(): RecipeSummary[] {
    const query = this.recipeSearch.trim().toLocaleLowerCase('de-DE');
    return this.recipes
      .filter(recipe => !query || `${recipe.name} ${recipe.description}`.toLocaleLowerCase('de-DE').includes(query))
      .sort((left, right) => {
        const leftMatch = left.category === this.dialogMealType ? 0 : 1;
        const rightMatch = right.category === this.dialogMealType ? 0 : 1;
        return leftMatch - rightMatch || left.name.localeCompare(right.name, 'de-DE');
      });
  }

  get totalMeals(): number {
    return this.days.reduce((total, day) => total + this.getMealCount(day), 0);
  }

  get plannedDays(): number {
    return this.days.filter(day => this.getMealCount(day) > 0).length;
  }

  get averageCalories(): number {
    return this.plannedDays
      ? Math.round(this.days.reduce((sum, day) => sum + this.getDayCalories(day), 0) / this.plannedDays)
      : 0;
  }

  get averageProtein(): number {
    return this.plannedDays
      ? Math.round(this.days.reduce((sum, day) => sum + this.getDayProtein(day), 0) / this.plannedDays)
      : 0;
  }

  get weeklyIngredientCount(): number {
    return this.allMeals().reduce((total, meal) => total + meal.ingredientCount, 0);
  }

  get nutritionReadyRecipeCount(): number {
    return this.recipes.filter(recipe => this.hasCompleteNutrition(recipe)).length;
  }

  get selectedAiMealTypes(): MealType[] {
    return [
      ...(this.planBreakfast ? ['breakfast' as MealType] : []),
      ...(this.planLunch ? ['lunch' as MealType] : []),
      ...(this.planDinner ? ['dinner' as MealType] : [])
    ];
  }

  get weeklyProductCount(): number {
    const products = new Set<string>();
    for (const meal of this.allMeals()) {
      const recipe = this.recipes.find(item => item.id === meal.recipeId);
      for (const ingredient of recipe?.ingredients ?? []) {
        products.add(
          ingredient.product != null
            ? `product:${ingredient.product}`
            : `name:${ingredient.name.trim().toLocaleLowerCase('de-DE')}`
        );
      }
    }
    return products.size;
  }

  get weeklyPantryIngredients(): RecipeIngredient[] {
    const unique = new Map<number, RecipeIngredient>();
    const plannedRecipeIds = new Set(
      this.allMeals().map(meal => meal.recipeId)
    );

    for (const recipe of this.recipes) {
      if (!plannedRecipeIds.has(recipe.id)) {
        continue;
      }
      for (const ingredient of recipe.ingredients ?? []) {
        const productId = this.pantryProductId(ingredient);
        if (
          productId !== null &&
          ingredient.product_detail?.is_common_pantry
        ) {
          unique.set(productId, ingredient);
        }
      }
    }

    return Array.from(unique.values())
      .sort((left, right) => left.name.localeCompare(right.name, 'de-DE'));
  }

  getMeals(day: PlannerDay, type: MealType): Meal[] {
    return day[type];
  }

  getMealCount(day: PlannerDay): number {
    return day.breakfast.length + day.lunch.length + day.dinner.length;
  }

  getDayCalories(day: PlannerDay): number {
    return Math.round(this.dayMeals(day).reduce((total, meal) => total + meal.calories, 0));
  }

  getDayProtein(day: PlannerDay): number {
    return Math.round(this.dayMeals(day).reduce((total, meal) => total + meal.protein, 0));
  }

  addMeal(dayIndex: number, type: MealType): void {
    this.openMealDialog(dayIndex, type, null);
  }

  openMeal(dayIndex: number, type: MealType, meal: Meal): void {
    this.openMealDialog(dayIndex, type, meal);
  }

  closeMealDialog(): void {
    if (this.isSaving) {
      return;
    }
    this.mealDialogOpen = false;
    this.recipeSearch = '';
    this.dialogEntry = null;
  }

  chooseRecipe(recipe: RecipeSummary): void {
    this.selectedRecipeId = recipe.id;
    if (!this.dialogEntry) {
      this.selectedServings = Math.max(Number(recipe.servings) || 1, 1);
    }
  }

  saveMeal(): void {
    const day = this.dialogDay;
    if (!day || this.selectedRecipeId == null) {
      this.showFeedback('Bitte wähle zuerst ein Rezept aus.', 'error');
      return;
    }

    this.isSaving = true;
    const payload = {
      date: day.dateKey,
      meal_type: this.dialogMealType,
      servings: Math.max(Math.round(Number(this.selectedServings) || 1), 1),
      recipe: this.selectedRecipeId
    };
    const request = this.dialogEntry
      ? this.plannerService.updateEntry(this.dialogEntry.entryId, payload)
      : this.plannerService.saveEntry(payload);
    request
      .pipe(finalize(() => { this.isSaving = false; }))
      .subscribe({
        next: entry => {
          const meals = day[this.dialogMealType];
          const updatedMeal = this.entryToMeal(entry);
          const index = meals.findIndex(meal => meal.entryId === entry.id);
          if (index >= 0) meals[index] = updatedMeal;
          else meals.push(updatedMeal);
          this.loadRecipeDetails([entry]);
          this.mealDialogOpen = false;
          this.showFeedback(`${this.dialogMealLabel} wurde gespeichert.`, 'success');
        },
        error: error => this.showFeedback(
          this.apiError(error, 'Die Mahlzeit konnte nicht gespeichert werden.'),
          'error'
        )
      });
  }

  removeMeal(): void {
    const day = this.dialogDay;
    const entry = this.dialogEntry;
    if (!day || !entry) {
      return;
    }
    this.isSaving = true;
    this.plannerService.deleteEntry(entry.entryId)
      .pipe(finalize(() => { this.isSaving = false; }))
      .subscribe({
        next: () => {
          day[this.dialogMealType] = day[this.dialogMealType]
            .filter(meal => meal.entryId !== entry.entryId);
          this.mealDialogOpen = false;
          this.showFeedback('Die Mahlzeit wurde aus dem Wochenplan entfernt.', 'success');
        },
        error: error => this.showFeedback(
          this.apiError(error, 'Die Mahlzeit konnte nicht entfernt werden.'),
          'error'
        )
      });
  }

  openSelectedRecipe(): void {
    if (this.selectedRecipeId == null) {
      return;
    }
    this.mealDialogOpen = false;
    void this.router.navigate(['/main/recipe-list', this.selectedRecipeId]);
  }

  createRecipe(): void {
    this.mealDialogOpen = false;
    void this.router.navigate(['/main/recipe-list/create']);
  }

  previousWeek(): void {
    this.changeWeek(-7);
  }

  nextWeek(): void {
    this.changeWeek(7);
  }

  goToCurrentWeek(): void {
    this.weekStart = this.startOfWeek(new Date());
    this.buildDays();
    this.selectedDayIndex = this.todayIndexForWeek();
    this.loadEntries();
  }

  openAiPlannerDialog(): void {
    if (!this.nutritionReadyRecipeCount) {
      this.showFeedback(
        'Für die KI-Planung brauchst du mindestens ein Rezept mit vollständig berechneten Nährwerten.',
        'error'
      );
      return;
    }
    this.clearFeedback();
    this.aiPlannerDialogOpen = true;
  }

  closeAiPlannerDialog(): void {
    if (this.isGenerating) {
      return;
    }
    this.aiPlannerDialogOpen = false;
  }

  generateWeek(): void {
    const mealTypes = this.selectedAiMealTypes;
    if (!mealTypes.length) {
      this.showFeedback('Wähle mindestens eine Mahlzeit für die Planung aus.', 'error');
      return;
    }
    this.isGenerating = true;
    this.clearFeedback();
    this.plannerService.generateWeek(this.weekStartKey, this.weekEndKey, {
      meal_types: mealTypes,
      daily_calorie_target: this.positiveNumberOrNull(this.aiDailyCalorieTarget),
      daily_protein_target: this.positiveNumberOrNull(this.aiDailyProteinTarget),
      max_recipe_repeats: Math.min(Math.max(Math.round(Number(this.aiMaxRecipeRepeats) || 2), 1), 7),
      servings: Math.min(Math.max(Math.round(Number(this.aiServings) || 2), 1), 30),
      overwrite: this.aiOverwrite
    })
      .pipe(finalize(() => { this.isGenerating = false; }))
      .subscribe({
        next: response => {
          this.aiPlannerDialogOpen = false;
          this.applyEntries(response.entries);
          this.showFeedback(response.message, 'success');
        },
        error: error => this.showFeedback(
          this.apiError(error, 'Die Woche konnte nicht automatisch geplant werden.'),
          'error'
        )
      });
  }

  createShoppingList(): void {
    if (!this.totalMeals) {
      this.showFeedback('Plane zuerst mindestens eine Mahlzeit.', 'error');
      return;
    }

    if (this.isLoadingRecipeDetails) {
      this.showFeedback('Die Zutaten der geplanten Rezepte werden noch geladen.', 'error');
      return;
    }

    if (this.weeklyPantryIngredients.length) {
      this.includedPantryProductIds.clear();
      this.pantryDialogOpen = true;
      return;
    }

    this.submitShoppingList();
  }

  closePantryDialog(): void {
    if (this.isCreatingShoppingList) {
      return;
    }
    this.pantryDialogOpen = false;
    this.includedPantryProductIds.clear();
  }

  pantryProductId(ingredient: RecipeIngredient): number | null {
    return ingredient.product ?? ingredient.product_detail?.id ?? null;
  }

  isPantryIngredientIncluded(ingredient: RecipeIngredient): boolean {
    const productId = this.pantryProductId(ingredient);
    return productId !== null && this.includedPantryProductIds.has(productId);
  }

  togglePantryIngredient(ingredient: RecipeIngredient): void {
    const productId = this.pantryProductId(ingredient);
    if (productId === null) {
      return;
    }
    if (this.includedPantryProductIds.has(productId)) {
      this.includedPantryProductIds.delete(productId);
    } else {
      this.includedPantryProductIds.add(productId);
    }
  }

  confirmShoppingList(): void {
    this.submitShoppingList(Array.from(this.includedPantryProductIds));
  }

  private submitShoppingList(includedPantryProductIds?: number[]): void {
    this.isCreatingShoppingList = true;
    this.clearFeedback();
    this.plannerService.createShoppingList(
      this.weekStartKey,
      this.weekEndKey,
      includedPantryProductIds
    )
      .pipe(finalize(() => { this.isCreatingShoppingList = false; }))
      .subscribe({
        next: response => {
          this.pantryDialogOpen = false;
          this.includedPantryProductIds.clear();
          this.showFeedback(response.message, 'success');
          void this.router.navigate(['/main/shopping-list']);
        },
        error: error => this.showFeedback(
          this.apiError(error, 'Der Wocheneinkauf konnte nicht erstellt werden.'),
          'error'
        )
      });
  }

  categoryLabel(category: string): string {
    return {
      breakfast: 'Frühstück',
      lunch: 'Mittagessen',
      dinner: 'Abendessen',
      snack: 'Snack',
      dessert: 'Dessert',
      other: 'Sonstiges'
    }[category] ?? 'Sonstiges';
  }

  recipeNutrition(recipe: RecipeSummary): string {
    const calories = this.numberValue(recipe.calories);
    const protein = this.numberValue(recipe.protein);
    if (!this.hasCompleteNutrition(recipe)) {
      return 'Noch keine Nährwerte berechnet';
    }
    return `${Math.round(calories)} kcal · ${this.roundNumber(protein)} g Protein`;
  }

  hasCompleteNutrition(recipe: RecipeSummary): boolean {
    return [
      recipe.calories,
      recipe.protein,
      recipe.carbohydrates,
      recipe.fat,
      recipe.fiber
    ].every(value => value !== null && value !== undefined && value !== '');
  }

  private loadInitialData(): void {
    this.isLoading = true;
    this.clearFeedback();
    forkJoin({
      recipes: this.recipeService.getRecipeSummaries(),
      entries: this.plannerService.getEntries(this.weekStartKey, this.weekEndKey)
    })
      .pipe(finalize(() => { this.isLoading = false; }))
      .subscribe({
        next: ({ recipes, entries }) => {
          this.recipes = recipes;
          this.applyEntries(entries);
          this.selectedDayIndex = this.todayIndexForWeek();
        },
        error: error => this.showFeedback(
          this.apiError(error, 'Der Wochenplan konnte nicht geladen werden.'),
          'error'
        )
      });
  }

  private positiveNumberOrNull(value: number | null): number | null {
    const parsed = Number(value);
    return value !== null && Number.isFinite(parsed) && parsed > 0
      ? Math.round(parsed)
      : null;
  }

  private loadEntries(): void {
    this.isLoading = true;
    this.clearFeedback();
    this.plannerService.getEntries(this.weekStartKey, this.weekEndKey)
      .pipe(finalize(() => { this.isLoading = false; }))
      .subscribe({
        next: entries => this.applyEntries(entries),
        error: error => this.showFeedback(
          this.apiError(error, 'Der Wochenplan konnte nicht geladen werden.'),
          'error'
        )
      });
  }

  private openMealDialog(dayIndex: number, type: MealType, meal: Meal | null): void {
    this.dialogDayIndex = dayIndex;
    this.dialogMealType = type;
    this.recipeSearch = '';
    this.dialogEntry = meal;
    this.selectedRecipeId = meal?.recipeId ?? null;
    this.selectedServings = meal?.servings ?? 1;

    if (!meal) {
      const preferred = this.recipes.find(recipe => recipe.category === type) ?? this.recipes[0];
      if (preferred) {
        this.selectedRecipeId = preferred.id;
        this.selectedServings = Math.max(Number(preferred.servings) || 1, 1);
      }
    }
    this.mealDialogOpen = true;
  }

  private changeWeek(offset: number): void {
    this.weekStart = this.addDays(this.weekStart, offset);
    this.buildDays();
    this.selectedDayIndex = this.todayIndexForWeek();
    this.loadEntries();
  }

  private buildDays(): void {
    const fullNames = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];
    const shortNames = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
    const todayKey = this.dateKey(new Date());
    this.days = fullNames.map((fullName, index) => {
      const dayDate = this.addDays(this.weekStart, index);
      return {
        fullName,
        shortName: shortNames[index],
        date: new Intl.DateTimeFormat('de-DE', { day: 'numeric', month: 'long' }).format(dayDate),
        dateKey: this.dateKey(dayDate),
        dayNumber: dayDate.getDate(),
        isToday: this.dateKey(dayDate) === todayKey,
        breakfast: [],
        lunch: [],
        dinner: []
      };
    });
  }

  private applyEntries(entries: WeeklyPlanEntry[]): void {
    this.buildDays();
    const daysByDate = new Map(this.days.map(day => [day.dateKey, day]));
    for (const entry of entries) {
      const day = daysByDate.get(entry.date);
      if (day) {
        day[entry.meal_type].push(this.entryToMeal(entry));
      }
    }
    this.loadRecipeDetails(entries);
  }

  private loadRecipeDetails(entries: WeeklyPlanEntry[]): void {
    const recipeIds = Array.from(new Set(entries.map(entry => entry.recipe)));
    const missingIds = recipeIds.filter(recipeId => {
      const recipe = this.recipes.find(item => item.id === recipeId);
      return recipe !== undefined && recipe.ingredients === undefined;
    });
    if (!missingIds.length) {
      return;
    }

    this.isLoadingRecipeDetails = true;
    this.recipeService.getRecipesByIds(missingIds)
      .pipe(finalize(() => { this.isLoadingRecipeDetails = false; }))
      .subscribe({
        next: details => {
          const detailsById = new Map(details.map(recipe => [recipe.id, recipe]));
          this.recipes = this.recipes.map(summary => {
            const detail = detailsById.get(summary.id);
            return detail ? { ...summary, ...detail } : summary;
          });
        },
        error: error => console.error('Rezeptzutaten konnten nicht geladen werden:', error)
      });
  }

  private entryToMeal(entry: WeeklyPlanEntry): Meal {
    const recipe = entry.recipe_detail;
    return {
      entryId: entry.id,
      recipeId: recipe.id,
      name: recipe.name,
      image: recipe.image_url || this.categoryImage(recipe.category),
      imagePosition: recipe.image_url
        ? `${recipe.image_position_x ?? 50}% ${recipe.image_position_y ?? 50}%`
        : '50% 50%',
      calories: this.numberValue(recipe.calories),
      protein: this.numberValue(recipe.protein),
      carbohydrates: this.numberValue(recipe.carbohydrates),
      fat: this.numberValue(recipe.fat),
      servings: entry.servings,
      ingredientCount: recipe.ingredient_count ?? 0
    };
  }

  private categoryImage(category: string): string {
    if (category === 'breakfast') {
      return 'assets/images/home/home-ai-food.webp';
    }
    if (category === 'lunch') {
      return 'assets/images/home/home-food.webp';
    }
    return 'assets/images/home/home-recipes.webp';
  }

  private dayMeals(day: PlannerDay): Meal[] {
    return [...day.breakfast, ...day.lunch, ...day.dinner];
  }

  private allMeals(): Meal[] {
    return this.days.flatMap(day => this.dayMeals(day));
  }

  private get weekStartKey(): string {
    return this.dateKey(this.weekStart);
  }

  private get weekEndKey(): string {
    return this.dateKey(this.addDays(this.weekStart, 6));
  }

  private startOfWeek(value: Date): Date {
    const result = new Date(value.getFullYear(), value.getMonth(), value.getDate(), 12);
    result.setDate(result.getDate() - ((result.getDay() + 6) % 7));
    return result;
  }

  private addDays(value: Date, days: number): Date {
    const result = new Date(value.getFullYear(), value.getMonth(), value.getDate(), 12);
    result.setDate(result.getDate() + days);
    return result;
  }

  private dateKey(value: Date): string {
    const month = String(value.getMonth() + 1).padStart(2, '0');
    const day = String(value.getDate()).padStart(2, '0');
    return `${value.getFullYear()}-${month}-${day}`;
  }

  private monthName(value: Date): string {
    return new Intl.DateTimeFormat('de-DE', { month: 'long' }).format(value);
  }

  private todayIndexForWeek(): number {
    const todayKey = this.dateKey(new Date());
    const index = this.days.findIndex(day => day.dateKey === todayKey);
    return index >= 0 ? index : 0;
  }

  private numberValue(value: number | string | null | undefined): number {
    const parsed = Number(value ?? 0);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  private roundNumber(value: number): string {
    return Number(value.toFixed(1)).toLocaleString('de-DE');
  }

  private showFeedback(message: string, kind: FeedbackKind): void {
    this.feedbackMessage = message;
    this.feedbackKind = kind;
  }

  private clearFeedback(): void {
    this.feedbackMessage = '';
    this.feedbackKind = '';
  }

  private apiError(error: unknown, fallback: string): string {
    const response = error as { error?: { detail?: string } };
    return response?.error?.detail || fallback;
  }
}
