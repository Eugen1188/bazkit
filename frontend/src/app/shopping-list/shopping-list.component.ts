import {
  Component,
  OnInit
} from '@angular/core';

import {
  CommonModule
} from '@angular/common';

import {
  FormsModule
} from '@angular/forms';

import {
  SavedList
} from '../services/saved-list.service';

import {
  ShoppingList,
  ShoppingListItem,
  ShoppingListService
} from '../services/shopping-list.service';

import {
  AddToShoppingListModalComponent
} from '../components/add-to-shopping-list-modal/add-to-shopping-list-modal.component';

import {
  AddProductModalComponent
} from '../components/add-product-modal/add-product-modal.component';

import {
  AddSavedListModalComponent
} from '../components/add-saved-list-modal/add-saved-list-modal.component';

import {
  AddRecipeIngredientsModalComponent
} from '../components/add-recipe-ingredients-modal/add-recipe-ingredients-modal.component';


@Component({
  selector: 'app-shopping-list',

  standalone: true,

  imports: [
    CommonModule,
    FormsModule,
    AddToShoppingListModalComponent,
    AddProductModalComponent,
    AddSavedListModalComponent,
    AddRecipeIngredientsModalComponent
  ],

  templateUrl:
    './shopping-list.component.html',

  styleUrl:
    './shopping-list.component.scss'
})
export class ShoppingListComponent
implements OnInit {

  items:
    ShoppingListItem[] = [];


  isLoading = true;

  isSaving = false;

  errorMessage = '';


  isAddOptionsOpen =
    false;

  isAddProductOpen =
    false;

  isAddSavedListOpen =
    false;

  isAddRecipeOpen =
    false;


  constructor(
    private shoppingListService:
      ShoppingListService
  ) {}


  ngOnInit(): void {

    this.loadShoppingList();
  }


  loadShoppingList(): void {

    this.isLoading =
      true;

    this.errorMessage =
      '';


    this.shoppingListService
      .getShoppingList()
      .subscribe({

        next: (
          shoppingList
        ) => {

          this.items =
            shoppingList.items ?? [];

          this.isLoading =
            false;
        },


        error: (
          error
        ) => {

          console.error(
            'Einkaufsliste konnte nicht geladen werden:',
            error
          );

          this.errorMessage =
            'Die Einkaufsliste konnte nicht geladen werden.';

          this.isLoading =
            false;
        }

      });
  }


  openAddOptions(): void {

    this.isAddOptionsOpen =
      true;
  }


  closeAllModals(): void {

    this.isAddOptionsOpen =
      false;

    this.isAddProductOpen =
      false;

    this.isAddSavedListOpen =
      false;

    this.isAddRecipeOpen =
      false;
  }


  openProductModal(): void {

    this.closeAllModals();

    this.isAddProductOpen =
      true;
  }


  openSavedListModal(): void {

    this.closeAllModals();

    this.isAddSavedListOpen =
      true;
  }


  openRecipeModal(): void {

    this.closeAllModals();

    this.isAddRecipeOpen =
      true;
  }


  addSingleItem(
    item: ShoppingListItem
  ): void {

    this.items.push(
      item
    );

    this.closeAllModals();
  }


  addSavedListToShoppingList(
    list: SavedList
  ): void {

    this.isSaving =
      true;

    this.errorMessage =
      '';


    this.shoppingListService
      .addSavedList(
        list.id
      )
      .subscribe({

        next: (
          shoppingList
        ) => {

          this.items =
            shoppingList.items ?? [];

          this.isSaving =
            false;

          this.closeAllModals();
        },


        error: (
          error
        ) => {

          console.error(
            'Gespeicherte Liste konnte nicht übernommen werden:',
            error
          );

          this.isSaving =
            false;

          this.errorMessage =
            'Die Liste konnte nicht zur Einkaufsliste hinzugefügt werden.';
        }

      });
  }


  recipeAdded(
    shoppingList: ShoppingList
  ): void {

    this.items =
      shoppingList.items ?? [];

    this.closeAllModals();
  }


  toggleItem(
    item: ShoppingListItem
  ): void {

    const newValue =
      !item.is_checked;


    this.shoppingListService
      .updateItem(
        item.id,
        {
          is_checked:
            newValue
        }
      )
      .subscribe({

        next: (
          updatedItem
        ) => {

          const index =
            this.items.findIndex(
              current =>
                current.id ===
                updatedItem.id
            );


          if (
            index !== -1
          ) {

            this.items[index] =
              updatedItem;
          }
        },


        error: (
          error
        ) => {

          console.error(
            'Produktstatus konnte nicht gespeichert werden:',
            error
          );
        }

      });
  }


  removeItem(
    index: number
  ): void {

    const item =
      this.items[index];


    if (
      !item
    ) {
      return;
    }


    this.shoppingListService
      .deleteItem(
        item.id
      )
      .subscribe({

        next: () => {

          this.items.splice(
            index,
            1
          );
        },


        error: (
          error
        ) => {

          console.error(
            'Produkt konnte nicht entfernt werden:',
            error
          );
        }

      });
  }


  clearShoppingList(): void {

    if (
      this.items.length === 0
    ) {
      return;
    }


    const shouldClear =
      confirm(
        'Möchtest du die komplette Einkaufsliste leeren?'
      );


    if (
      !shouldClear
    ) {
      return;
    }


    this.shoppingListService
      .clearShoppingList()
      .subscribe({

        next: () => {

          this.items = [];
        },


        error: (
          error
        ) => {

          console.error(
            'Einkaufsliste konnte nicht geleert werden:',
            error
          );
        }

      });
  }


  get completedCount():
    number {

    return this.items
      .filter(
        item =>
          item.is_checked
      )
      .length;
  }


  get progress():
    number {

    if (
      this.items.length === 0
    ) {
      return 0;
    }


    return Math.round(
      (
        this.completedCount /
        this.items.length
      ) * 100
    );
  }
}