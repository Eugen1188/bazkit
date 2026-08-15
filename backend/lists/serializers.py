import { CommonModule } from '@angular/common';
import {
  Component,
  OnInit
} from '@angular/core';

import { FormsModule } from '@angular/forms';

import {
  ActivatedRoute,
  Router,
  RouterLink
} from '@angular/router';

import {
  CreateSavedListPayload,
  SavedListService
} from '../../services/saved-list.service';

interface Product {
  id?: number;
  name: string;
  quantity: number;
  unit: string;
  note?: string;
}

interface ProductSuggestion {
  name: string;
  quantity: number;
  unit: string;
}

@Component({
  selector: 'app-saved-list-edit',
  standalone: true,

  imports: [
    CommonModule,
    FormsModule,
    RouterLink
  ],

  templateUrl:
    './saved-list-edit.component.html',

  styleUrls: [
    '../create-list/create-list.component.scss',
    './saved-list-edit.component.scss'
  ]
})

export class SavedListEditComponent
  implements OnInit {

  listId: number | null = null;

  listName = '';

  productName = '';

  productQuantity: number | null = 1;

  productUnit = 'Stück';

  products: Product[] = [];

  isLoading = true;

  isSaving = false;

  errorMessage = '';

  units = [
    'Stück',
    'g',
    'kg',
    'ml',
    'Liter',
    'Packung',
    'Dose',
    'Glas',
    'Becher',
    'Bund'
  ];

  suggestions: ProductSuggestion[] = [
    {
      name: 'Milch',
      quantity: 1,
      unit: 'Liter'
    },
    {
      name: 'Eier',
      quantity: 10,
      unit: 'Stück'
    },
    {
      name: 'Brot',
      quantity: 1,
      unit: 'Stück'
    },
    {
      name: 'Tomaten',
      quantity: 500,
      unit: 'g'
    },
    {
      name: 'Gurken',
      quantity: 1,
      unit: 'Stück'
    },
    {
      name: 'Äpfel',
      quantity: 6,
      unit: 'Stück'
    },
    {
      name: 'Käse',
      quantity: 200,
      unit: 'g'
    },
    {
      name: 'Hähnchen',
      quantity: 500,
      unit: 'g'
    }
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private savedListService: SavedListService
  ) {}

  ngOnInit(): void {

    const id = Number(
      this.route.snapshot.paramMap.get('id')
    );

    if (!id) {
      this.errorMessage =
        'Liste konnte nicht gefunden werden';

      this.isLoading = false;

      return;
    }

    this.listId = id;

    this.loadList();
  }

  loadList(): void {

    if (!this.listId) {
      return;
    }

    this.savedListService
      .getSavedList(this.listId)
      .subscribe({

        next: (list) => {

          this.listName = list.title;

          this.products =
            (list.items ?? []).map(
              item => ({
                id: item.id,
                name:
                  item.name ||
                  item.product_name ||
                  '',
                quantity:
                  Number(item.quantity),
                unit:
                  item.unit,
                note:
                  item.note ?? ''
              })
            );

          this.isLoading = false;
        },

        error: (error) => {

          console.error(error);

          this.errorMessage =
            'Die Liste konnte nicht geladen werden';

          this.isLoading = false;
        }
      });
  }

  addProduct(
    suggestion?: ProductSuggestion
  ): void {

    const name =
      suggestion?.name ??
      this.productName.trim();

    const quantity =
      suggestion?.quantity ??
      this.productQuantity;

    const unit =
      suggestion?.unit ??
      this.productUnit;

    if (
      !name ||
      quantity === null ||
      quantity <= 0 ||
      !unit
    ) {
      return;
    }

    this.products.push({
      name,
      quantity,
      unit,
      note: ''
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
      !this.listId ||
      !this.listName.trim()
    ) {
      return;
    }

    const payload:
      CreateSavedListPayload = {

      title:
        this.listName.trim(),

      items:
        this.products.map(
          product => ({
            id: product.id,
            name: product.name,
            quantity: product.quantity,
            unit: product.unit,
            note: product.note ?? ''
          })
        )
    };

    this.isSaving = true;

    this.savedListService
      .updateSavedList(
        this.listId,
        payload
      )
      .subscribe({

        next: () => {

          this.isSaving = false;

          this.router.navigate([
            '/main/saved-list',
            this.listId
          ]);
        },

        error: (error) => {

          console.error(error);

          this.errorMessage =
            'Die Änderungen konnten nicht gespeichert werden';

          this.isSaving = false;
        }
      });
  }

  cancel(): void {

    this.router.navigate([
      '/main/saved-list',
      this.listId
    ]);
  }

  private resetProductForm(): void {

    this.productName = '';

    this.productQuantity = 1;

    this.productUnit = 'Stück';
  }
}