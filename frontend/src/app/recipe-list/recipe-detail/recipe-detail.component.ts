import {
  Component,
  OnInit
} from '@angular/core';

import {
  CommonModule
} from '@angular/common';

import {
  ActivatedRoute,
  Router
} from '@angular/router';

import {
  Recipe,
  RecipeService
} from '../../services/recipe.service';


@Component({
  selector: 'app-recipe-detail',
  standalone: true,

  imports: [
    CommonModule
  ],

  templateUrl:
    './recipe-detail.component.html',

  styleUrl:
    './recipe-detail.component.scss'
})
export class RecipeDetailComponent
implements OnInit {

  recipe: Recipe | null = null;

  isLoading = true;

  errorMessage = '';


  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private recipeService: RecipeService
  ) {}


  ngOnInit(): void {

    const id = Number(
      this.route.snapshot.paramMap.get('id')
    );

    if (!id) {

      this.errorMessage =
        'Das Rezept konnte nicht gefunden werden.';

      this.isLoading = false;

      return;
    }

    this.loadRecipe(id);
  }


  loadRecipe(
    id: number
  ): void {

    this.isLoading = true;
    this.errorMessage = '';

    this.recipeService
      .getRecipe(id)
      .subscribe({

        next: (recipe) => {

          this.recipe = recipe;

          this.isLoading = false;
        },

        error: (error) => {

          console.error(
            'Rezept konnte nicht geladen werden:',
            error
          );

          this.errorMessage =
            'Das Rezept konnte nicht geladen werden.';

          this.isLoading = false;
        }

      });
  }


  goBack(): void {

    this.router.navigate([
      '/main/recipe-list'
    ]);
  }


  getCategoryLabel(
    category: string
  ): string {

    const categories:
      Record<string, string> = {

      breakfast: 'Frühstück',
      lunch: 'Mittagessen',
      dinner: 'Abendessen',
      snack: 'Snack',
      dessert: 'Dessert',
      other: 'Sonstiges'
    };

    return (
      categories[category] ??
      'Sonstiges'
    );
  }


  get preparationSteps():
    string[] {

    if (
      !this.recipe?.instructions
    ) {
      return [];
    }

    return this.recipe.instructions
      .split('\n')
      .map(
        step =>
          step.replace(
            /^\d+\.\s*/,
            ''
          ).trim()
      )
      .filter(
        step =>
          step.length > 0
      );
  }
}