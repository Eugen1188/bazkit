import { Component, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'app-add-to-shopping-list-modal',
  standalone: true,
  imports: [],
  templateUrl: './add-to-shopping-list-modal.component.html',
  styleUrl: './add-to-shopping-list-modal.component.scss'
})
export class AddToShoppingListModalComponent {

  @Output() close = new EventEmitter<void>();
  @Output() addProduct = new EventEmitter<void>();
  @Output() addSavedList = new EventEmitter<void>();
  @Output() addRecipe = new EventEmitter<void>();

}
