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

  selectedListId: number | null = null;


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

    /*
     * WICHTIG:
     *
     * Wir laden die Liste NICHT noch einmal
     * mit getSavedList().
     *
     * getSavedLists() liefert über deinen
     * Django SavedListSerializer bereits:
     *
     * id
     * title
     * item_count
     * items
     *
     * Dadurch brauchen wir keinen zweiten
     * API Request.
     */

    this.selectedListId =
      list.id;

    this.selectList.emit(
      list
    );
  }


  getProductPreview(
    list: SavedList
  ): string {

    const items =
      list.items ?? [];

    if (items.length === 0) {
      return 'Keine Produkte';
    }

    const names =
      items
        .slice(0, 3)
        .map(
          item =>
            item.name ||
            item.product_name
        )
        .filter(Boolean);

    const preview =
      names.join(', ');

    if (items.length > 3) {
      return `${preview}, ...`;
    }

    return preview;
  }


  closeModal(): void {
    this.close.emit();
  }
}