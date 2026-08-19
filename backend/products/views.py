import {
  CommonModule
} from '@angular/common';

import {
  Component,
  OnDestroy
} from '@angular/core';

import {
  FormsModule
} from '@angular/forms';

import {
  Router,
  RouterLink
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
  ProductSuggestion
} from '../../services/product.service';


interface Product {

  id?: number;

  name: string;

  quantity: number;

  unit: string;

  note?: string;
}


@Component({
  selector:
    'app-create-list',

  standalone: true,

  imports: [
    CommonModule,
    FormsModule,
    RouterLink
  ],

  templateUrl:
    './create-list.component.html',

  styleUrl:
    './create-list.component.scss'
})
export class CreateListComponent
implements OnDestroy {

  listName = '';

  productName = '';

  productQuantity:
    number | null = 1;

  productUnit =
    'Stück';


  products:
    Product[] = [];


  isSaving =
    false;

  errorMessage =
    '';


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
            250
          ),

          distinctUntilChanged(),

          switchMap(
            query => {

              this.isSearchingProducts =
                true;

              return (
                this.productService
                  .searchProducts(
                    query
                  )
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
              'Produktsuche fehlgeschlagen:',
              error
            );

            this.productSuggestions =
              [];

            this.isSearchingProducts =
              false;

            this.isSuggestionsOpen =
              false;
          }

        });
  }


  ngOnDestroy():
    void {

    this.productSearchSubscription
      .unsubscribe();
  }


  onProductNameChange(
    value: string
  ): void {

    this.productName =
      value;


    const query =
      value.trim();


    this.externalSearchDone =
      false;

    this.externalSearchError =
      '';


    if (
      query.length < 2
    ) {

      this.productSuggestions =
        [];

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

    this.productName =
      product.name;


    if (
      product.default_unit
      &&
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
  }


  searchExternal():
    void {

    const query =
      this.productName
        .trim();


    if (
      query.length < 3
      ||
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


  openSuggestions():
    void {

    if (
      this.productName
        .trim()
        .length >= 2
    ) {

      this.isSuggestionsOpen =
        true;
    }
  }


  closeSuggestions():
    void {

    window.setTimeout(
      () => {

        this.isSuggestionsOpen =
          false;
      },
      200
    );
  }


  addProduct():
    void {

    const name =
      this.productName
        .trim();


    if (
      !name
      ||
      this.productQuantity === null
      ||
      this.productQuantity <= 0
      ||
      !this.productUnit
    ) {

      return;
    }


    this.products.push({
      name,

      quantity:
        this.productQuantity,

      unit:
        this.productUnit
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


  createList():
    void {

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

            name:
              product.name,

            quantity:
              product.quantity,

            unit:
              product.unit,

            note:
              product.note ?? ''
          })
        )
    };


    this.isSaving =
      true;

    this.errorMessage =
      '';


    this.savedListService
      .createSavedList(
        payload
      )
      .subscribe({

        next: () => {

          this.isSaving =
            false;

          this.router.navigate([
            '/main/saved-list'
          ]);
        },


        error: (
          error
        ) => {

          console.error(
            'Fehler beim Erstellen der Liste:',
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
              error.error.title[0];

            return;
          }


          this.errorMessage =
            'Die Liste konnte nicht erstellt werden.';
        }

      });
  }


  cancel():
    void {

    this.router.navigate([
      '/main/saved-list'
    ]);
  }


  private resetProductForm():
    void {

    this.productName =
      '';

    this.productQuantity =
      1;

    this.productUnit =
      'Stück';

    this.productSuggestions =
      [];

    this.isSuggestionsOpen =
      false;

    this.externalSearchDone =
      false;

    this.externalSearchError =
      '';
  }
}