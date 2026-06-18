import { Component, EventEmitter, Output } from '@angular/core';


@Component({
  selector: 'app-add-product-modal',
  standalone: true,
  imports: [],
  templateUrl: './add-product-modal.component.html',
  styleUrl: './add-product-modal.component.scss'
})
export class AddProductModalComponent {
   @Output() close = new EventEmitter<void>();

}
