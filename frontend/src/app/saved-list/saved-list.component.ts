import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-saved-list',
  standalone: true,
  imports: [RouterModule],
  templateUrl: './saved-list.component.html',
  styleUrl: './saved-list.component.scss'
})
export class SavedListComponent {}