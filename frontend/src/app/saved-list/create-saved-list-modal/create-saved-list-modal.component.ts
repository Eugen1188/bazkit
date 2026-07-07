import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

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

  constructor(private router: Router) {}

  cancel(): void {
    this.close.emit();
  }

  create(): void {
    if (!this.listName.trim()) {
      return;
    }

    // Später kommt diese ID vom Backend zurück.
    const fakeCreatedListId = 1;

    this.close.emit();

    this.router.navigate(['/main/saved-list', fakeCreatedListId]);
  }
}