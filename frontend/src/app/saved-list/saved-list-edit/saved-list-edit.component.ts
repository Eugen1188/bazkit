import { CommonModule } from '@angular/common';

import {
  Component,
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
  CreateSavedListPayload,
  SavedListService
} from '../../services/saved-list.service';
import { UiIconComponent } from '../../components/ui-icon/ui-icon.component';
import { UserSettingsService } from '../../services/user-settings.service';
import { UiQuantityInputComponent } from '../../components/ui-quantity-input/ui-quantity-input.component';


interface Product {
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
    FormsModule,
    UiIconComponent,
    UiQuantityInputComponent
  ],

  templateUrl:
    './saved-list-edit.component.html',

  styleUrl:
    './saved-list-edit.component.scss'
})
export class SavedListEditComponent
implements OnInit {

  listId:
    number | null = null;

  communityPostId: number | null = null;


  listName = '';

  productName = '';

  productQuantity:
    number | null = 1;

  productUnit =
    'Stück';

  productNote = '';


  products:
    Product[] = [];


  isLoading = true;

  isSaving = false;

  errorMessage = '';


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

  constructor(
    private route:
      ActivatedRoute,

    private router:
      Router,

    private savedListService:
      SavedListService,

    private userSettings:
      UserSettingsService
  ) {

    this.productUnit =
      this.userSettings.current.shopping_default_unit;
  }


  ngOnInit(): void {

    const communityPost = Number(this.route.snapshot.queryParamMap.get('communityPost'));
    this.communityPostId = communityPost > 0 ? communityPost : null;

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


  loadList(): void {

    if (
      !this.listId
    ) {
      return;
    }


    const cached = this.savedListService.getCachedSavedList(this.listId);
    if (cached?.can_edit) this.applyList(cached);
    this.isLoading = !cached;

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

          if (!list.can_edit) {
            this.router.navigate(['/main/saved-list', this.listId]);
            return;
          }

          this.applyList(list);
        },


        error: (
          error
        ) => {

          console.error(
            'Fehler beim Laden der Liste:',
            error
          );

          if (!cached) this.errorMessage = 'Die Liste konnte nicht geladen werden.';

          this.isLoading =
            false;
        }

      });
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
      product: null,

      name,

      quantity:
        this.productQuantity,

      unit:
        this.productUnit,

      note:
        this.productNote.trim()
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

    if (!navigator.onLine) {
      this.saveOffline(payload);
      return;
    }


    this.savedListService
      .updateSavedList(
        this.listId,
        payload
      )
      .subscribe({

        next: () => {

          this.isSaving =
            false;

          if (this.communityPostId) {
            this.router.navigate(['/main/community', this.communityPostId]);
          } else {
            this.router.navigate(['/main/saved-list', this.listId]);
          }
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

          if (error?.status === 0 || error?.name === 'TimeoutError') {
            this.saveOffline(payload);
            return;
          }


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

    if (this.communityPostId) {
      this.router.navigate(['/main/community', this.communityPostId]);
      return;
    }

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
      this.userSettings.current.shopping_default_unit;

    this.productNote =
      '';

  }

  private applyList(list: import('../../services/saved-list.service').SavedList): void {
    this.listName = list.title;
    this.products = (list.items ?? []).map(item => ({
      id: item.id,
      product: item.product ?? null,
      name: item.name || item.product_name || '',
      quantity: Number(item.quantity),
      unit: item.unit,
      note: item.note ?? '',
    }));
    this.isLoading = false;
  }

  private saveOffline(payload: CreateSavedListPayload): void {
    if (!this.listId) return;
    this.savedListService.queueSavedListUpdate(this.listId, payload);
    this.isSaving = false;
    void this.router.navigate(['/main/saved-list', this.listId]);
  }

}
