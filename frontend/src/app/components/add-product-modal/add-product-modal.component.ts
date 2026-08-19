import {
  CommonModule
} from '@angular/common';

import {
  Component,
  EventEmitter,
  OnDestroy,
  Output
} from '@angular/core';

import {
  FormsModule
} from '@angular/forms';

import {
  Subject,
  Subscription,
  debounceTime,
  distinctUntilChanged,
  switchMap
} from 'rxjs';

import {
  ProductService,
  ProductSuggestion
} from '../../services/product.service';

import {
  ShoppingListItem,
  ShoppingListService
} from '../../services/shopping-list.service';


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
implements OnDestroy {

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

  unit = 'Stück';

  note = '';


  suggestions:
    ProductSuggestion[] = [];


  isSearching = false;

  isSuggestionsOpen = false;

  isSaving = false;

  errorMessage = '';


  private searchSubject =
    new Subject<string>();


  private searchSubscription:
    Subscription;


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
    private productService:
      ProductService,

    private shoppingListService:
      ShoppingListService
  ) {

    this.searchSubscription =
      this.searchSubject
        .pipe(
          debounceTime(
            250
          ),

          distinctUntilChanged(),

          switchMap(
            query => {

              this.isSearching =
                true;

              return this.productService
                .searchProducts(
                  query
                );
            }
          )
        )
        .subscribe({

          next: (
            products
          ) => {

            this.suggestions =
              products;

            this.isSearching =
              false;

            this.isSuggestionsOpen =
              this.productName
                .trim()
                .length >= 2;
          },


          error: (
            error
          ) => {

            console.error(
              'Produktsuche fehlgeschlagen:',
              error
            );

            this.suggestions =
              [];

            this.isSearching =
              false;

            this.isSuggestionsOpen =
              false;
          }

        });
  }


  ngOnDestroy(): void {

    this.searchSubscription
      .unsubscribe();
  }


  onProductNameChange(
    value: string
  ): void {

    this.productName =
      value;


    const query =
      value.trim();


    if (
      query.length < 2
    ) {

      this.suggestions =
        [];

      this.isSuggestionsOpen =
        false;

      return;
    }


    this.isSuggestionsOpen =
      true;


    this.searchSubject.next(
      query
    );
  }


  selectProduct(
    product:
      ProductSuggestion
  ): void {

    this.productName =
      product.name;


    if (
      product.default_unit
      &&
      this.units.includes(
        product.default_unit
      )
    ) {

      this.unit =
        product.default_unit;
    }


    this.suggestions =
      [];

    this.isSuggestionsOpen =
      false;
  }


  openSuggestions(): void {

    if (
      this.productName
        .trim()
        .length >= 2
    ) {

      this.isSuggestionsOpen =
        true;
    }
  }


  closeSuggestions(): void {

    window.setTimeout(
      () => {

        this.isSuggestionsOpen =
          false;
      },
      180
    );
  }


  saveProduct(): void {

    const name =
      this.productName
        .trim();


    if (
      !name
      ||
      this.quantity === null
      ||
      this.quantity <= 0
      ||
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