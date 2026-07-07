import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-create-saved-list-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './create-saved-list-modal.component.html',
  styleUrl: './create-saved-list-modal.component.scss'
})
export class CreateSavedListModalComponent {

  @Output() close = new EventEmitter<void>();

  listName = '';

  cancel(): void {
    this.close.emit();
  }

  create(): void {

    if (!this.listName.trim()) {
      return;
    }

    console.log(this.listName);

    // später Backend aufrufen

    this.close.emit();
  }

}