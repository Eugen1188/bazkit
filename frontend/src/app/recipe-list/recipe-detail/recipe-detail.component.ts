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

import {
  parsePreparationSteps
} from '../preparation-steps';


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

  recipe:
    Recipe | null = null;

  isLoading = true;

  isDeleting = false;

  errorMessage = '';


  constructor(
    private route:
      ActivatedRoute,

    private router:
      Router,

    private recipeService:
      RecipeService
  ) {}


  ngOnInit(): void {

    const id = Number(
      this.route.snapshot
        .paramMap
        .get('id')
    );


    if (!id) {

      this.errorMessage =
        'Das Rezept konnte nicht gefunden werden.';

      this.isLoading =
        false;

      return;
    }


    this.loadRecipe(
      id
    );
  }


  loadRecipe(
    id: number
  ): void {

    this.isLoading =
      true;

    this.errorMessage =
      '';


    this.recipeService
      .getRecipe(
        id
      )
      .subscribe({

        next: (
          recipe: Recipe
        ) => {

          this.recipe =
            recipe;

          this.isLoading =
            false;
        },


        error: (
          error: unknown
        ) => {

          console.error(
            'Rezept konnte nicht geladen werden:',
            error
          );

          this.errorMessage =
            'Das Rezept konnte nicht geladen werden.';

          this.isLoading =
            false;
        }

      });
  }


  goBack(): void {

    this.router.navigate([
      '/main/recipe-list'
    ]);
  }


  editRecipe(): void {

    if (!this.recipe) {
      return;
    }


    this.router.navigate([
      '/main/recipe-list',
      this.recipe.id,
      'edit'
    ]);
  }


  deleteRecipe(): void {

    if (
      !this.recipe ||
      this.isDeleting
    ) {
      return;
    }


    const shouldDelete =
      confirm(
        `Möchtest du das Rezept "${this.recipe.name}" wirklich löschen?`
      );


    if (!shouldDelete) {
      return;
    }


    this.isDeleting =
      true;

    this.errorMessage =
      '';


    this.recipeService
      .deleteRecipe(
        this.recipe.id
      )
      .subscribe({

        next: () => {

          this.isDeleting =
            false;

          this.router.navigate([
            '/main/recipe-list'
          ]);
        },


        error: (
          error: unknown
        ) => {

          console.error(
            'Rezept konnte nicht gelöscht werden:',
            error
          );

          this.errorMessage =
            'Das Rezept konnte nicht gelöscht werden.';

          this.isDeleting =
            false;
        }

      });
  }


  getCategoryLabel(
    category: string
  ): string {

    const categories:
      Record<
        string,
        string
      > = {

      breakfast:
        'Frühstück',

      lunch:
        'Mittagessen',

      dinner:
        'Abendessen',

      snack:
        'Snack',

      dessert:
        'Dessert',

      other:
        'Sonstiges'
    };


    return (
      categories[
        category
      ]
      ?? 'Sonstiges'
    );
  }


  get preparationSteps():
    string[] {

    if (
      !this.recipe
        ?.instructions
    ) {
      return [];
    }


    return parsePreparationSteps(
      this.recipe.instructions
    );
  }
}
