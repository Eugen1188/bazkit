import {
  CommonModule
} from '@angular/common';

import {
  Component,
  EventEmitter,
  HostListener,
  OnDestroy,
  OnInit,
  Output
} from '@angular/core';

import {
  FormsModule
} from '@angular/forms';

import {
  ShoppingListItem,
  ShoppingListService
} from '../../services/shopping-list.service';
import { UserSettingsService } from '../../services/user-settings.service';


@Component({
  selector:
    'app-add-product-modal',

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
export class AddProductModalComponent
implements OnInit, OnDestroy {

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.closeModal();
  }

  @Output()
  close =
    new EventEmitter<void>();


  @Output()
  itemAdded =
    new EventEmitter<
      ShoppingListItem
    >();


  productName = '';

  quantity:
    number | null = 1;

  unit =
    'Stück';

  note =
    '';


  isSaving =
    false;

  errorMessage =
    '';


  units = [
    'Stück',
    'Stange',
    'Kopf',
    'Blatt',
    'Kugel',
    'Würfel',
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
    'Prise',
    'Zehe',
    'Scheibe',
    'Tasse'
  ];

  private previousBodyOverflow =
    '';


  constructor(
    private shoppingListService:
      ShoppingListService,

    private userSettings:
      UserSettingsService
  ) {

    this.unit =
      this.userSettings.current.shopping_default_unit;
  }


  ngOnInit(): void {

    this.previousBodyOverflow =
      document.body.style.overflow;

    document.body.style.overflow =
      'hidden';
  }


  ngOnDestroy(): void {
    document.body.style.overflow =
      this.previousBodyOverflow;
  }


  saveProduct(): void {

    const name =
      this.productName
        .trim();


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


    this.errorMessage =
      '';

    this.isSaving =
      true;


    this.shoppingListService
      .addItem({
        product: null,

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
