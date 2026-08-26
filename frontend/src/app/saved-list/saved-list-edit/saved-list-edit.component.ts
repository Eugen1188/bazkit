import { CommonModule } from '@angular/common';

import {
  Component,
  OnDestroy,
  OnInit
} from '@angular/core';

import {
  FormsModule
} from '@angular/forms';

import {
  ActivatedRoute,
  Router
} from '@angular/router';

import {
  Subject,
  Subscription,
  debounceTime,
  distinctUntilChanged,
  switchMap
} from 'rxjs';

import {
  CreateSavedListPayload,
  SavedListService
} from '../../services/saved-list.service';

import {
  ProductService,
  ProductSuggestion,
  PriceEstimate,
  PriceSnapshot
} from '../../services/product.service';


interface Product extends PriceSnapshot {
  id?: number;
  product?: number | null;
  name: string;
  quantity: number;
  unit: string;
  note?: string;
}


@Component({
  selector: 'app-saved-list-edit',

  standalone: true,

  imports: [
    CommonModule,
    FormsModule
  ],

  templateUrl:
    './saved-list-edit.component.html',

  styleUrl:
    './saved-list-edit.component.scss'
})
export class SavedListEditComponent
implements OnInit, OnDestroy {

  listId:
    number | null = null;


  listName = '';

  productName = '';

  productQuantity:
    number | null = 1;

  productUnit =
    'Stück';
  productPrice: number | null = null;
  priceEstimate: PriceEstimate | null = null;
  isPriceLoading = false;


  products:
    Product[] = [];


  isLoading = true;

  isSaving = false;

  errorMessage = '';


  productSuggestions:
    ProductSuggestion[] = [];

  isSearchingProducts =
    false;

  isSearchingExternal =
    false;

  isSuggestionsOpen =
    false;

  externalSearchDone =
    false;

  externalSearchError =
    '';

  selectedProduct:
    ProductSuggestion | null =
      null;


  private productSearchSubject =
    new Subject<string>();

  private productSearchSubscription:
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
    private route:
      ActivatedRoute,

    private router:
      Router,

    private savedListService:
      SavedListService,

    private productService:
      ProductService
  ) {

    this.productSearchSubscription =
      this.productSearchSubject
        .pipe(

          debounceTime(
            300
          ),

          distinctUntilChanged(),

          switchMap(
            query => {

              this.isSearchingProducts =
                true;

              this.externalSearchDone =
                false;

              this.externalSearchError =
                '';

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

            this.productSuggestions =
              products;

            this.isSearchingProducts =
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
              'Lokale Produktsuche fehlgeschlagen:',
              error
            );

            this.productSuggestions =
              [];

            this.isSearchingProducts =
              false;

            this.externalSearchError =
              'Die Produktsuche ist momentan nicht verfügbar.';

            this.isSuggestionsOpen =
              true;
          }

        });
  }


  ngOnInit(): void {

    const id =
      Number(
        this.route
          .snapshot
          .paramMap
          .get('id')
      );


    if (
      !id
    ) {

      this.errorMessage =
        'Liste konnte nicht gefunden werden.';

      this.isLoading =
        false;

      return;
    }


    this.listId =
      id;

    this.loadList();
  }


  ngOnDestroy(): void {

    this.productSearchSubscription
      .unsubscribe();
  }


  loadList(): void {

    if (
      !this.listId
    ) {
      return;
    }


    this.isLoading =
      true;

    this.errorMessage =
      '';


    this.savedListService
      .getSavedList(
        this.listId
      )
      .subscribe({

        next: (
          list
        ) => {

          this.listName =
            list.title;


          this.products =
            (
              list.items ??
              []
            )
              .map(
                item => ({
                  id:
                    item.id,

                  product:
                    item.product ?? null,

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

                  estimated_price: item.estimated_price,
                  price_source: item.price_source,
                  price_currency: item.price_currency,
                  price_date: item.price_date,
                  price_store: item.price_store,
                  price_sample_count: item.price_sample_count,
                  price_min: item.price_min,
                  price_max: item.price_max,
                  package_price: item.package_price,
                  package_quantity: item.package_quantity,
                  package_unit: item.package_unit
                })
              );


          this.isLoading =
            false;
        },


        error: (
          error
        ) => {

          console.error(
            'Fehler beim Laden der Liste:',
            error
          );

          this.errorMessage =
            'Die Liste konnte nicht geladen werden.';

          this.isLoading =
            false;
        }

      });
  }


  onProductNameChange(
    value: string
  ): void {

    this.productName =
      value;

    this.selectedProduct =
      null;
    this.productPrice = null;
    this.priceEstimate = null;


    const query =
      value.trim();


    this.productSuggestions =
      [];

    this.externalSearchDone =
      false;

    this.externalSearchError =
      '';


    if (
      query.length < 2
    ) {

      this.isSuggestionsOpen =
        false;

      return;
    }


    this.isSuggestionsOpen =
      true;


    this.productSearchSubject
      .next(
        query
      );
  }


  selectProductSuggestion(
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

      this.productUnit =
        product.default_unit;
    }


    this.productSuggestions =
      [];

    this.isSuggestionsOpen =
      false;

    this.externalSearchDone =
      false;

    this.externalSearchError =
      '';

    this.refreshProductPrice();
  }

  refreshProductPrice(): void {
    if (!this.selectedProduct || this.productQuantity === null || this.productQuantity <= 0) return;
    this.isPriceLoading = true;
    this.productService.estimatePrice(this.selectedProduct, this.productQuantity, this.productUnit, 'purchase')
      .subscribe({
        next: estimate => {
          this.isPriceLoading = false;
          this.priceEstimate = estimate;
          this.productPrice = estimate.available ? Number(estimate.estimated_price) : null;
        },
        error: () => { this.isPriceLoading = false; this.priceEstimate = null; },
      });
  }

  onManualPriceChange(): void { this.priceEstimate = null; }


  searchExternal(): void {

    const query =
      this.productName
        .trim();


    if (
      query.length < 4 ||
      this.isSearchingExternal
    ) {
      return;
    }


    this.isSearchingExternal =
      true;

    this.externalSearchDone =
      false;

    this.externalSearchError =
      '';


    this.productService
      .searchExternalProducts(
        query
      )
      .subscribe({

        next: (
          products
        ) => {

          this.productSuggestions =
            products;

          this.isSearchingExternal =
            false;

          this.externalSearchDone =
            true;

          this.isSuggestionsOpen =
            true;
        },


        error: (
          error
        ) => {

          console.error(
            'Externe Produktsuche fehlgeschlagen:',
            error
          );

          this.productSuggestions =
            [];

          this.isSearchingExternal =
            false;

          this.externalSearchDone =
            true;

          this.externalSearchError =
            'Die externe Suche ist momentan nicht verfügbar.';

          this.isSuggestionsOpen =
            true;
        }

      });
  }


  handleProductEnter(): void {

    if (
      this.productSuggestions.length > 0
    ) {

      this.selectProductSuggestion(
        this.productSuggestions[0]
      );

      return;
    }


    this.addProduct();
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
      200
    );
  }


  addProduct(): void {

    const name =
      this.productName
        .trim();


    if (
      !name ||
      this.productQuantity === null ||
      this.productQuantity <= 0 ||
      !this.productUnit
    ) {
      return;
    }


    this.products.push({
      product:
        this.selectedProduct?.id ?? null,

      name,

      quantity:
        this.productQuantity,

      unit:
        this.productUnit,

      note: ''
      , ...this.priceSnapshot()
    });


    this.resetProductForm();
  }


  removeProduct(
    index: number
  ): void {

    this.products.splice(
      index,
      1
    );
  }


  saveList(): void {

    if (
      !this.listId
    ) {
      return;
    }


    const trimmedListName =
      this.listName
        .trim();


    if (
      !trimmedListName
    ) {

      this.errorMessage =
        'Bitte geben Sie einen Listennamen ein.';

      return;
    }


    const payload:
      CreateSavedListPayload = {

      title:
        trimmedListName,

      items:
        this.products.map(
          product => ({

            ...product,

            id:
              product.id,

            product:
              product.product ?? null,

            name:
              product.name,

            quantity:
              product.quantity,

            unit:
              product.unit,

            note: product.note ?? ''
          })
        )
    };


    this.isSaving =
      true;

    this.errorMessage =
      '';


    this.savedListService
      .updateSavedList(
        this.listId,
        payload
      )
      .subscribe({

        next: () => {

          this.isSaving =
            false;

          this.router.navigate([
            '/main/saved-list',
            this.listId
          ]);
        },


        error: (
          error
        ) => {

          console.error(
            'Fehler beim Speichern der Liste:',
            error
          );

          this.isSaving =
            false;


          if (
            error.status === 401
          ) {

            this.errorMessage =
              'Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.';

            return;
          }


          if (
            error.error?.title
          ) {

            this.errorMessage =
              Array.isArray(
                error.error.title
              )
                ? error.error.title[0]
                : error.error.title;

            return;
          }


          this.errorMessage =
            'Die Änderungen konnten nicht gespeichert werden.';
        }

      });
  }


  cancel(): void {

    if (
      this.listId
    ) {

      this.router.navigate([
        '/main/saved-list',
        this.listId
      ]);

      return;
    }


    this.router.navigate([
      '/main/saved-list'
    ]);
  }


  private resetProductForm(): void {

    this.productName =
      '';

    this.productQuantity =
      1;

    this.productUnit =
      'Stück';
    this.productPrice = null;
    this.priceEstimate = null;
    this.isPriceLoading = false;

    this.productSuggestions =
      [];

    this.isSuggestionsOpen =
      false;

    this.isSearchingProducts =
      false;

    this.isSearchingExternal =
      false;

    this.externalSearchDone =
      false;

    this.externalSearchError =
      '';

    this.selectedProduct =
      null;
  }

  get estimatedTotal(): number {
    return this.products.reduce((sum, product) => sum + Number(product.estimated_price ?? 0), 0);
  }

  private priceSnapshot(): PriceSnapshot {
    const estimate = this.priceEstimate;
    if (!estimate) return { estimated_price: this.productPrice, price_source: this.productPrice === null ? '' : 'manual', price_currency: 'EUR' };
    return { ...estimate, estimated_price: this.productPrice };
  }
}
