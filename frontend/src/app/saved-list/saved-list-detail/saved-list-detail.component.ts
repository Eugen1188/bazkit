import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import {
  CreateSavedListPayload,
  SavedList,
  SavedListItem,
  SavedListService
} from '../../services/saved-list.service';

@Component({
  selector: 'app-saved-list-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink
  ],
  templateUrl: './saved-list-detail.component.html',
  styleUrl: './saved-list-detail.component.scss'
})
export class SavedListDetailComponent implements OnInit {

  savedList: SavedList | null = null;

  isLoading = true;
  isSaving = false;
  errorMessage = '';

  editingIndex: number | null = null;

  editItem: SavedListItem | null = null;

  units = [
    'Stück',
    'g',
    'kg',
    'ml',
    'Liter',
    'Packung',
    'Dose',
    'Glas',
    'Becher',
    'Bund'
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private savedListService: SavedListService
  ) { }

  ngOnInit(): void {
    const id = Number(
      this.route.snapshot.paramMap.get('id')
    );

    if (!id) {
      this.errorMessage =
        'Die Liste konnte nicht gefunden werden.';

      this.isLoading = false;

      return;
    }

    this.loadList(id);
  }

  loadList(id: number): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.savedListService
      .getSavedList(id)
      .subscribe({
        next: (list) => {
          this.savedList = list;
          this.isLoading = false;
        },

        error: (error) => {
          console.error(
            'Fehler beim Laden der Liste:',
            error
          );

          this.errorMessage =
            'Die Liste konnte nicht geladen werden.';

          this.isLoading = false;
        }
      });
  }

  goBack(): void {
    this.router.navigate([
      '/main/saved-list'
    ]);
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

  startEdit(
    index: number,
    item: SavedListItem
  ): void {

    this.editingIndex = index;

    this.editItem = {
      ...item
    };
  }

  cancelEdit(): void {
    this.editingIndex = null;
    this.editItem = null;
  }

  saveEdit(): void {

    if (
      !this.savedList ||
      this.editingIndex === null ||
      !this.editItem ||
      !this.editItem.id
    ) {
      return;
    }

    if (
      !this.editItem.name.trim() ||
      this.editItem.quantity <= 0 ||
      !this.editItem.unit
    ) {
      return;
    }

    this.isSaving = true;

    this.savedListService
      .updateSavedListItem(
        this.savedList.id,
        this.editItem.id,
        this.editItem
      )
      .subscribe({

        next: (updatedItem) => {

          if (
            this.savedList?.items &&
            this.editingIndex !== null
          ) {
            this.savedList.items[
              this.editingIndex
            ] = updatedItem;
          }

          this.editingIndex = null;
          this.editItem = null;
          this.isSaving = false;
        },

        error: (error) => {

          console.error(
            'Produkt konnte nicht gespeichert werden:',
            error
          );

          this.isSaving = false;
        }
      });
  }

  deleteItem(index: number): void {

    if (!this.savedList?.items) {
      return;
    }

    const item = this.savedList.items[index];

    if (!item?.id) {
      return;
    }

    const shouldDelete = confirm(
      `Möchtest du "${item.name}" wirklich löschen?`
    );

    if (!shouldDelete) {
      return;
    }

    this.savedListService
      .deleteSavedListItem(
        this.savedList.id,
        item.id
      )
      .subscribe({

        next: () => {

          this.savedList!.items =
            this.savedList!.items!.filter(
              (_, i) => i !== index
            );
        },

        error: (error) => {

          console.error(
            'Produkt konnte nicht gelöscht werden:',
            error
          );
        }
      });
  }
}