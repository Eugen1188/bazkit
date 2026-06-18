import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-add-saved-list-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './add-saved-list-modal.component.html',
  styleUrl: './add-saved-list-modal.component.scss'
})
export class AddSavedListModalComponent {

    @Output() close = new EventEmitter<void>();

  savedLists = [
    { name: 'Wocheneinkauf', count: 24 },
    { name: 'Frühstück', count: 8 },
    { name: 'Grillen & BBQ', count: 15 },
    { name: 'Partyabend', count: 12 }
  ];
}
