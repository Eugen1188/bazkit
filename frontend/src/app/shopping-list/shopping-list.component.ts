import {
  Component,
  HostListener,
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
  ListShareService
} from '../services/list-share.service';

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


type ShoppingFilter = 'all' | 'open' | 'completed';

interface ShoppingCategoryGroup {
  key: string;
  label: string;
  order: number;
  items: ShoppingListItem[];
}


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

  shareMessage = '';

  activeFilter: ShoppingFilter = 'all';


  isAddOptionsOpen =
    false;

  isAddProductOpen =
    false;

  isAddSavedListOpen =
    false;

  isAddRecipeOpen =
    false;

  isListMenuOpen =
    false;


  constructor(
    private shoppingListService:
      ShoppingListService,

    private listShareService:
      ListShareService
  ) { }


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

    this.isListMenuOpen =
      false;

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


  toggleListMenu(
    event: MouseEvent
  ): void {

    event.stopPropagation();

    this.isListMenuOpen =
      !this.isListMenuOpen;
  }


  @HostListener(
    'document:click'
  )
  closeListMenu(): void {

    this.isListMenuOpen =
      false;
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


  async shareShoppingList(): Promise<void> {

    this.isListMenuOpen =
      false;

    this.shareMessage =
      '';


    try {

      const result =
        await this.listShareService
          .shareList(
            'Einkaufsliste',
            this.items.map(
              item => ({
                name:
                  item.name,

                quantity:
                  item.quantity,

                unit:
                  item.unit,

                note:
                  item.note,

                isChecked:
                  item.is_checked
              })
            )
          );


      if (
        result === 'copied'
      ) {

        this.showShareMessage(
          'Liste wurde in die Zwischenablage kopiert.'
        );
      }

    } catch (
    error
    ) {

      console.error(
        'Liste konnte nicht geteilt werden:',
        error
      );

      this.showShareMessage(
        'Die Liste konnte nicht geteilt werden.'
      );
    }
  }


  private showShareMessage(
    message: string
  ): void {

    this.shareMessage =
      message;


    window.setTimeout(
      () => {

        if (
          this.shareMessage ===
          message
        ) {

          this.shareMessage =
            '';
        }

      },
      3000
    );
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
    item: ShoppingListItem
  ): void {
    this.shoppingListService
      .deleteItem(
        item.id
      )
      .subscribe({

        next: () => {
          this.items = this.items.filter(current => current.id !== item.id);
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

    this.isListMenuOpen =
      false;


    if (
      this.items.length === 0
    ) {
      return;
    }


    const shouldClear =
      confirm(
        'Möchtest du wirklich alle Produkte aus der Einkaufsliste entfernen?'
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

  get estimatedTotal(): number {
    return Math.round(this.items.reduce((sum, item) => sum + Number(item.estimated_price ?? 0), 0) * 100) / 100;
  }

  setFilter(filter: ShoppingFilter): void {
    this.activeFilter = filter;
  }

  get categoryGroups(): ShoppingCategoryGroup[] {
    const filteredItems = this.items.filter(item => {
      if (this.activeFilter === 'open') return !item.is_checked;
      if (this.activeFilter === 'completed') return item.is_checked;
      return true;
    });
    const groups = new Map<string, ShoppingCategoryGroup>();
    for (const item of filteredItems) {
      const key = item.shopping_category || 'other';
      const group = groups.get(key) ?? {
        key,
        label: item.shopping_category_label || 'Sonstiges',
        order: item.shopping_category_order ?? 90,
        items: []
      };
      group.items.push(item);
      groups.set(key, group);
    }
    return [...groups.values()]
      .sort((left, right) => left.order - right.order || left.label.localeCompare(right.label, 'de-DE'))
      .map(group => ({
        ...group,
        items: [...group.items].sort((left, right) =>
          Number(left.is_checked) - Number(right.is_checked) || left.name.localeCompare(right.name, 'de-DE')
        )
      }));
  }
}
