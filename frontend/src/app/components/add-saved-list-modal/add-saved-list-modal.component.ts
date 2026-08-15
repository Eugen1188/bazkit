import {
  Component,
  EventEmitter,
  OnInit,
  Output
} from '@angular/core';

import { CommonModule } from '@angular/common';

import {
  SavedList,
  SavedListService
} from '../../services/saved-list.service';


@Component({
  selector: 'app-add-saved-list-modal',
  standalone: true,
  imports: [
    CommonModule
  ],
  templateUrl:
    './add-saved-list-modal.component.html',
  styleUrl:
    './add-saved-list-modal.component.scss'
})
export class AddSavedListModalComponent
implements OnInit {

  @Output()
  close = new EventEmitter<void>();

  @Output()
  selectList =
    new EventEmitter<SavedList>();


  savedLists: SavedList[] = [];

  isLoading = true;

  errorMessage = '';


  constructor(
    private savedListService:
      SavedListService
  ) {}


  ngOnInit(): void {
    this.loadSavedLists();
  }


  loadSavedLists(): void {

    this.isLoading = true;

    this.errorMessage = '';

    this.savedListService
      .getSavedLists()
      .subscribe({

        next: (lists) => {

          this.savedLists = lists;

          this.isLoading = false;
        },

        error: (error) => {

          console.error(
            'Fehler beim Laden der gespeicherten Listen:',
            error
          );

          this.errorMessage =
            'Die gespeicherten Listen konnten nicht geladen werden.';

          this.isLoading = false;
        }
      });
  }


  chooseList(
    list: SavedList
  ): void {

    this.savedListService
      .getSavedList(list.id)
      .subscribe({

        next: (fullList) => {

          this.selectList.emit(
            fullList
          );
        },

        error: (error) => {

          console.error(
            'Liste konnte nicht geladen werden:',
            error
          );
        }
      });
  }


  closeModal(): void {
    this.close.emit();
  }
}