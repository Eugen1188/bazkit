import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

interface Product {
  name: string;
  quantity: number;
  unit: string;
}

interface ProductSuggestion {
  name: string;
  quantity: number;
  unit: string;
}

@Component({
  selector: 'app-create-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './create-list.component.html',
  styleUrl: './create-list.component.scss'
})
export class CreateListComponent {
  listName = '';

  productName = '';
  productQuantity: number | null = 1;
  productUnit = 'Stück';

  products: Product[] = [];

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
    { name: 'Milch', quantity: 1, unit: 'Liter' },
    { name: 'Eier', quantity: 10, unit: 'Stück' },
    { name: 'Brot', quantity: 1, unit: 'Stück' },
    { name: 'Tomaten', quantity: 500, unit: 'g' },
    { name: 'Gurken', quantity: 1, unit: 'Stück' },
    { name: 'Äpfel', quantity: 6, unit: 'Stück' },
    { name: 'Käse', quantity: 200, unit: 'g' },
    { name: 'Hähnchen', quantity: 500, unit: 'g' }
  ];

  constructor(private router: Router) {}

  addProduct(suggestion?: ProductSuggestion): void {
    const name = suggestion?.name ?? this.productName.trim();
    const quantity = suggestion?.quantity ?? this.productQuantity;
    const unit = suggestion?.unit ?? this.productUnit;

    if (!name || quantity === null || quantity <= 0 || !unit) {
      return;
    }

    this.products.push({
      name,
      quantity,
      unit
    });

    this.resetProductForm();
  }

  removeProduct(index: number): void {
    this.products.splice(index, 1);
  }

  createList(): void {
    const trimmedListName = this.listName.trim();

    if (!trimmedListName) {
      return;
    }

    const newList = {
      name: trimmedListName,
      products: this.products
    };

    console.log('Neue gespeicherte Liste:', newList);

    // Später:
    // this.savedListService.createList(newList).subscribe(...)

    const fakeId = 1;
    this.router.navigate(['/main/saved-list', fakeId]);
  }

  private resetProductForm(): void {
    this.productName = '';
    this.productQuantity = 1;
    this.productUnit = 'Stück';
  }
}