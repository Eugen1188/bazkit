import {
  Component,
  OnInit
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import {
  SavedList
} from '../services/saved-list.service';

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


interface ShoppingListItem {
  name: string;
  quantity: number;
  unit: string;
  note?: string;
  isChecked: boolean;
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

  /*
   * Unter diesem Namen speichern
   * wir die Einkaufsliste im Browser.
   */
  private readonly storageKey =
    'bazkit_shopping_list';


  items: ShoppingListItem[] = [];


  isAddOptionsOpen = false;

  isAddProductOpen = false;

  isAddSavedListOpen = false;

  isAddRecipeOpen = false;


  /*
   * Beim Öffnen der Seite werden
   * vorhandene Produkte geladen.
   */
  ngOnInit(): void {
    this.loadShoppingList();
  }


  /*
   * Einkaufsliste aus LocalStorage laden
   */
  private loadShoppingList(): void {

    const savedItems =
      localStorage.getItem(
        this.storageKey
      );

    if (!savedItems) {
      this.items = [];
      return;
    }

    try {

      const parsedItems =
        JSON.parse(savedItems);

      if (
        Array.isArray(parsedItems)
      ) {

        this.items =
          parsedItems.map(
            item => ({
              name:
                item.name ?? '',

              quantity:
                Number(
                  item.quantity
                ) || 0,

              unit:
                item.unit ?? '',

              note:
                item.note ?? '',

              isChecked:
                Boolean(
                  item.isChecked
                )
            })
          );

      }

    } catch (error) {

      console.error(
        'Einkaufsliste konnte nicht aus LocalStorage geladen werden:',
        error
      );

      this.items = [];

    }
  }


  /*
   * Einkaufsliste speichern
   */
  private saveShoppingList(): void {

    localStorage.setItem(
      this.storageKey,
      JSON.stringify(
        this.items
      )
    );

  }


  /*
   * Haupt-Auswahl öffnen
   */
  openAddOptions(): void {

    this.isAddOptionsOpen =
      true;

  }


  /*
   * Alle Modals schließen
   */
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


  /*
   * Einzelnes Produkt hinzufügen
   */
  openProductModal(): void {

    this.closeAllModals();

    this.isAddProductOpen =
      true;

  }


  /*
   * Gespeicherte Liste auswählen
   */
  openSavedListModal(): void {

    this.closeAllModals();

    this.isAddSavedListOpen =
      true;

  }


  /*
   * Rezept auswählen
   */
  openRecipeModal(): void {

    this.closeAllModals();

    this.isAddRecipeOpen =
      true;

  }


  /*
   * Produkte einer gespeicherten
   * Liste übernehmen
   */
  addSavedListToShoppingList(
    list: SavedList
  ): void {

    const newItems =
      (list.items ?? [])
        .map(
          item => ({

            name:
              item.name ||
              item.product_name ||
              '',

            quantity:
              Number(
                item.quantity
              ),

            unit:
              item.unit,

            note:
              item.note ?? '',

            isChecked:
              false

          })
        )
        .filter(
          item =>
            item.name
              .trim()
              .length > 0
        );


    this.items.push(
      ...newItems
    );


    /*
     * WICHTIG:
     * Nach dem Hinzufügen speichern
     */
    this.saveShoppingList();


    this.closeAllModals();

  }


  /*
   * Produkt abhaken /
   * wieder öffnen
   */
  toggleItem(
    item: ShoppingListItem
  ): void {

    item.isChecked =
      !item.isChecked;


    /*
     * Status speichern
     */
    this.saveShoppingList();

  }


  /*
   * Produkt entfernen
   */
  removeItem(
    index: number
  ): void {

    this.items.splice(
      index,
      1
    );


    /*
     * Neue Liste speichern
     */
    this.saveShoppingList();

  }


  /*
   * Anzahl erledigter Produkte
   */
  get completedCount():
    number {

    return this.items
      .filter(
        item =>
          item.isChecked
      )
      .length;

  }


  /*
   * Fortschritt in Prozent
   */
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


  /*
   * Optional:
   * komplette Einkaufsliste löschen
   *
   * Können wir später mit einem
   * "Liste leeren"-Button benutzen.
   */
  clearShoppingList(): void {

    this.items = [];

    localStorage.removeItem(
      this.storageKey
    );

  }
}