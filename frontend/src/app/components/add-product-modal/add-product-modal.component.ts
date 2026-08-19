import {
  Component,
  EventEmitter,
  Output
} from '@angular/core';

import {
  CommonModule
} from '@angular/common';

import {
  FormsModule
} from '@angular/forms';

import {
  ShoppingListItem,
  ShoppingListService
} from '../../services/shopping-list.service';


@Component({
  selector: 'app-add-product-modal',

  standalone: true,

  imports: [
    CommonModule,
    FormsModule
  ],

  templateUrl:
    './add-product-modal.component.html',

  styleUrl:
    './add-product-modal.component.scss'
})
export class AddProductModalComponent {

  @Output()
  close =
    new EventEmitter<void>();


  @Output()
  itemAdded =
    new EventEmitter<ShoppingListItem>();


  productName = '';

  quantity:
    number | null = 1;

  unit = 'Stück';

  note = '';

  isSaving = false;

  errorMessage = '';


  units = [
    'Stück',
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
    'Prise'
  ];


  constructor(
    private shoppingListService:
      ShoppingListService
  ) {}


  saveProduct(): void {

    const name =
      this.productName.trim();


    if (
      !name ||
      this.quantity === null ||
      this.quantity <= 0 ||
      !this.unit
    ) {

      this.errorMessage =
        'Bitte gib Produkt, Menge und Einheit an.';

      return;
    }


    this.errorMessage = '';

    this.isSaving = true;


    this.shoppingListService
      .addItem({
        name,
        quantity:
          this.quantity,
        unit:
          this.unit,
        note:
          this.note.trim()
      })
      .subscribe({

        next: (
          item
        ) => {

          this.isSaving =
            false;

          this.itemAdded.emit(
            item
          );
        },


        error: (
          error
        ) => {

          console.error(
            'Produkt konnte nicht hinzugefügt werden:',
            error
          );

          this.errorMessage =
            'Das Produkt konnte nicht hinzugefügt werden.';

          this.isSaving =
            false;
        }

      });
  }


  closeModal(): void {

    if (
      this.isSaving
    ) {
      return;
    }

    this.close.emit();
  }
}