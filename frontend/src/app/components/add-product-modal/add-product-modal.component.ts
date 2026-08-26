import {
  CommonModule
} from '@angular/common';

import {
  Component,
  EventEmitter,
  OnDestroy,
  OnInit,
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
  ProductSuggestion,
  PriceEstimate
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
implements OnInit, OnDestroy {

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
  estimatedPrice: number | null = null;
  priceEstimate: PriceEstimate | null = null;
  isPriceLoading = false;


  suggestions:
    ProductSuggestion[] = [];

  selectedProduct:
    ProductSuggestion | null =
      null;


  isSearching =
    false;

  isSuggestionsOpen =
    false;

  isSaving =
    false;

  errorMessage =
    '';


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


  private searchSubject =
    new Subject<string>();


  private searchSubscription:
    Subscription;


  private previousBodyOverflow =
    '';


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


  ngOnInit(): void {

    this.previousBodyOverflow =
      document.body.style.overflow;

    document.body.style.overflow =
      'hidden';
  }


  ngOnDestroy(): void {

    this.searchSubscription
      .unsubscribe();


    document.body.style.overflow =
      this.previousBodyOverflow;
  }


  onProductNameChange(
    value: string
  ): void {

    this.productName =
      value;

    this.selectedProduct =
      null;
    this.estimatedPrice = null;
    this.priceEstimate = null;


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

    this.selectedProduct =
      product;

    this.productName =
      product.name;


    if (
      product.default_unit &&
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

    this.refreshPrice();
  }

  refreshPrice(): void {
    if (!this.selectedProduct || this.quantity === null || this.quantity <= 0) return;
    this.isPriceLoading = true;
    this.productService.estimatePrice(this.selectedProduct, this.quantity, this.unit, 'purchase').subscribe({
      next: estimate => {
        this.isPriceLoading = false;
        this.priceEstimate = estimate;
        this.estimatedPrice = estimate.available ? Number(estimate.estimated_price) : null;
      },
      error: () => { this.isPriceLoading = false; this.priceEstimate = null; },
    });
  }

  onManualPriceChange(): void { this.priceEstimate = null; }


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
        product:
          this.selectedProduct?.id ?? null,

        name,

        quantity:
          this.quantity,

        unit:
          this.unit,

        note:
          this.note.trim(),

        estimated_price: this.estimatedPrice,
        price_source: this.priceEstimate?.price_source ?? (this.estimatedPrice === null ? '' : 'manual'),
        price_currency: this.priceEstimate?.price_currency ?? 'EUR',
        price_date: this.priceEstimate?.price_date ?? null,
        price_store: this.priceEstimate?.price_store ?? '',
        price_sample_count: this.priceEstimate?.price_sample_count ?? 0,
        price_min: this.priceEstimate?.price_min ?? null,
        price_max: this.priceEstimate?.price_max ?? null,
        package_price: this.priceEstimate?.package_price ?? null,
        package_quantity: this.priceEstimate?.package_quantity ?? null,
        package_unit: this.priceEstimate?.package_unit ?? ''
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
