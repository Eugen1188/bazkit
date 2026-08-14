import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import {
  Router
} from '@angular/router';

import {
  SavedList,
  SavedListService
} from '../services/saved-list.service';

@Component({
  selector: 'app-saved-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule
  ],
  templateUrl: './saved-list.component.html',
  styleUrl: './saved-list.component.scss'
})
export class SavedListComponent implements OnInit {

  savedLists: SavedList[] = [];

  isLoading = true;

  errorMessage = '';

  openedMenuId: number | null = null;

  constructor(
  private savedListService:
    SavedListService,
  private router: Router
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
            'Fehler beim Laden der Listen:',
            error
          );

          this.errorMessage =
            'Die Listen konnten nicht geladen werden.';

          this.isLoading = false;
        }
      });
  }

  editList(
  event: MouseEvent,
  list: SavedList
): void {

  event.preventDefault();
  event.stopPropagation();

  this.router.navigate([
    '/main/saved-list',
    list.id,
    'edit'
  ]);
}

  toggleMenu(
    event: MouseEvent,
    listId: number
  ): void {
    event.stopPropagation();

    this.openedMenuId =
      this.openedMenuId === listId
        ? null
        : listId;
  }

  deleteList(
    event: MouseEvent,
    list: SavedList
  ): void {

    event.preventDefault();
    event.stopPropagation();

    const shouldDelete = confirm(
      `Möchtest du "${list.title}" wirklich löschen?`
    );

    if (!shouldDelete) {
      return;
    }

    this.savedListService
      .deleteSavedList(list.id)
      .subscribe({
        next: () => {
          this.savedLists =
            this.savedLists.filter(
              item => item.id !== list.id
            );
        },

        error: (error) => {
          console.error(
            'Liste konnte nicht gelöscht werden:',
            error
          );
        }
      });
  }

  formatDate(date: string): string {
    return new Intl.DateTimeFormat(
      'de-DE',
      {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      }
    ).format(new Date(date));
  }
}