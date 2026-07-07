import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

interface SavedListProduct {
  id: number;
  name: string;
  amount: string;
  note?: string;
}

@Component({
  selector: 'app-saved-list-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './saved-list-detail.component.html',
  styleUrl: './saved-list-detail.component.scss'
})
export class SavedListDetailComponent {
  listId: string | null = null;

  listName = 'Neue Liste';
  products: SavedListProduct[] = [];

  constructor(private route: ActivatedRoute) {
    this.listId = this.route.snapshot.paramMap.get('id');

    // später vom Backend laden:
    // GET /api/saved-lists/:id/
  }

  addProduct(): void {
    console.log('Produkt hinzufügen');
  }
}