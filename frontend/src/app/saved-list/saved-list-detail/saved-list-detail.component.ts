import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import {
  SavedList,
  SavedListService
} from '../../services/saved-list.service';

@Component({
  selector: 'app-saved-list-detail',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink
  ],
  templateUrl: './saved-list-detail.component.html',
  styleUrl: './saved-list-detail.component.scss'
})
export class SavedListDetailComponent implements OnInit {

  savedList: SavedList | null = null;

  isLoading = true;
  errorMessage = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private savedListService: SavedListService
  ) {}

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
}