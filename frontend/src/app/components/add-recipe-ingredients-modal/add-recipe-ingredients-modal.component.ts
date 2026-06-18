import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';


@Component({
  selector: 'app-add-recipe-ingredients-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './add-recipe-ingredients-modal.component.html',
  styleUrl: './add-recipe-ingredients-modal.component.scss'
})
export class AddRecipeIngredientsModalComponent {

    @Output() close = new EventEmitter<void>();

  recipes = [
    { name: 'Spaghetti Bolognese', portions: 4 },
    { name: 'Gemüsecurry mit Reis', portions: 2 },
    { name: 'Ofengemüse mit Feta', portions: 2 },
    { name: 'Pancakes', portions: 3 }
  ];
}
