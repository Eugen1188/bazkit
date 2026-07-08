import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

interface Product {
  name: string;
  amount: string;
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

  products: Product[] = [];

  suggestions = [
    'Milch',
    'Eier',
    'Brot',
    'Tomaten',
    'Gurken',
    'Äpfel',
    'Käse',
    'Hähnchen'
  ];

  constructor(private router: Router) {}

  addProduct(name?: string): void {
    const finalName = name || this.productName.trim();

    if (!finalName) {
      return;
    }

    this.products.push({
      name: finalName,
      amount: '1 Stück'
    });

    this.productName = '';
  }

  removeProduct(index: number): void {
    this.products.splice(index, 1);
  }

  createList(): void {
    if (!this.listName.trim()) {
      return;
    }

    console.log({
      name: this.listName,
      products: this.products
    });

    const fakeId = 1;
    this.router.navigate(['/main/saved-list', fakeId]);
  }
}