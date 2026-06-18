import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

import { AddToShoppingListModalComponent } from '../components/add-to-shopping-list-modal/add-to-shopping-list-modal.component';
import { AddProductModalComponent } from '../components/add-product-modal/add-product-modal.component';
import { AddSavedListModalComponent } from '../components/add-saved-list-modal/add-saved-list-modal.component';
import { AddRecipeIngredientsModalComponent } from '../components/add-recipe-ingredients-modal/add-recipe-ingredients-modal.component';

@Component({
  selector: 'app-shopping-list',
  standalone: true,
  imports: [CommonModule, AddToShoppingListModalComponent, AddProductModalComponent, AddSavedListModalComponent, AddRecipeIngredientsModalComponent],
  templateUrl: './shopping-list.component.html',
  styleUrl: './shopping-list.component.scss'
})
export class ShoppingListComponent {
  items: any[] = [];

  isAddOptionsOpen = false;
  isAddProductOpen = false;
  isAddSavedListOpen = false;
  isAddRecipeOpen = false;

  openAddOptions(): void {
    this.isAddOptionsOpen = true;
  }

  closeAllModals(): void {
    this.isAddOptionsOpen = false;
    this.isAddProductOpen = false;
    this.isAddSavedListOpen = false;
    this.isAddRecipeOpen = false;
  }

  openProductModal(): void {
    this.closeAllModals();
    this.isAddProductOpen = true;
  }

  openSavedListModal(): void {
    this.closeAllModals();
    this.isAddSavedListOpen = true;
  }

  openRecipeModal(): void {
    this.closeAllModals();
    this.isAddRecipeOpen = true;
  }

}
