import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CreateSavedListModalComponent } from './create-saved-list-modal/create-saved-list-modal.component';


@Component({
  selector: 'app-saved-list',
  standalone: true,
  imports: [CommonModule, CreateSavedListModalComponent],
  templateUrl: './saved-list.component.html',
  styleUrl: './saved-list.component.scss'
})
export class SavedListComponent {

  isCreateListOpen = false;

openCreateList(): void {
  this.isCreateListOpen = true;
}

closeCreateList(): void {
  this.isCreateListOpen = false;
}

}
