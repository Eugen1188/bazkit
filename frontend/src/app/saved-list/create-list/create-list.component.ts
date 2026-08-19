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
  catchError,
  debounceTime,
  distinctUntilChanged,
  map,
  of,
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
            350
          ),

          distinctUntilChanged(),

          switchMap(
            query => {

              this.isSearchingProducts =
                true;

              this.isSearchingExternal =
                false;

              this.externalSearchDone =
                false;

              this.externalSearchError =
                '';


              return this.productService
                .searchProducts(
                  query
                )
                .pipe(

                  switchMap(
                    localProducts => {

                      this.isSearchingProducts =
                        false;


                      if (
                        localProducts.length > 0
                      ) {

                        return of(
                          localProducts
                        );
                      }


                      if (
                        query.length < 3
                      ) {

                        return of(
                          []
                        );
                      }


                      this.isSearchingExternal =
                        true;


                      return this.productService
                        .searchExternalProducts(
                          query
                        )
                        .pipe(

                          map(
                            externalProducts => {

                              this.isSearchingExternal =
                                false;

                              this.externalSearchDone =
                                true;

                              return (
                                externalProducts
                              );
                            }
                          ),

                          catchError(
                            error => {

                              console.error(
                                'Externe Produktsuche fehlgeschlagen:',
                                error
                              );


                              this.isSearchingExternal =
                                false;

                              this.externalSearchDone =
                                true;

                              this.externalSearchError =
                                'Die externe Suche ist momentan nicht verfügbar.';


                              return of(
                                []
                              );
                            }
                          )

                        );
                    }
                  ),

                  catchError(
                    error => {

                      console.error(
                        'Lokale Produktsuche fehlgeschlagen:',
                        error
                      );


                      this.isSearchingProducts =
                        false;

                      this.isSearchingExternal =
                        false;

                      this.externalSearchError =
                        'Die Produktsuche ist momentan nicht verfügbar.';


                      return of(
                        []
                      );
                    }
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

            this.isSuggestionsOpen =
              this.productName
                .trim()
                .length >= 2;
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


    this.selectedProduct =
      null;


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


  handleProductEnter():
    void {

    if (
      this.productSuggestions.length > 0
    ) {

      this.selectProductSuggestion(
        this.productSuggestions[0]
      );

      return;
    }


    if (
      this.isSearchingProducts
      ||
      this.isSearchingExternal
    ) {

      return;
    }


    this.addProduct();
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


    if (
      this.selectedProduct?.source
      === 'external'
    ) {

      this.productService
        .saveExternalProduct(
          this.selectedProduct
        )
        .subscribe({

          error: (
            error
          ) => {

            console.error(
              'Externes Produkt konnte nicht lokal gespeichert werden:',
              error
            );
          }

        });
    }


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

}