import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';


export type UiIconName =
  | 'sparkles'
  | 'check'
  | 'plate'
  | 'clock'
  | 'users'
  | 'ingredient'
  | 'steps'
  | 'idea'
  | 'cart'
  | 'list';


@Component({
  selector: 'app-ui-icon',
  standalone: true,
  imports: [CommonModule],
  template: `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <ng-container [ngSwitch]="name">
        <ng-container *ngSwitchCase="'sparkles'">
          <path d="M12 3l1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6L12 3Z"></path>
          <path d="M18 15l.8 2.2L21 18l-2.2.8L18 21l-.8-2.2L15 18l2.2-.8L18 15Z"></path>
        </ng-container>
        <path *ngSwitchCase="'check'" d="M5 12l4 4 10-10"></path>
        <ng-container *ngSwitchCase="'plate'">
          <circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="3.5"></circle>
          <path d="M3 4v7M1.5 4v4a1.5 1.5 0 0 0 3 0V4M20 4v16M17.5 4v7"></path>
        </ng-container>
        <ng-container *ngSwitchCase="'clock'">
          <circle cx="12" cy="13" r="8"></circle><path d="M12 9v4l3 2M9 3h6"></path>
        </ng-container>
        <ng-container *ngSwitchCase="'users'">
          <circle cx="9" cy="8" r="3"></circle><path d="M3 20v-2a6 6 0 0 1 12 0v2M17 11a3 3 0 0 1 0 6M19 20v-1"></path>
        </ng-container>
        <path *ngSwitchCase="'ingredient'" d="M7 8c4-2 8 2 6 6l-5 7c-1 1-3 0-3-1L4 11c0-2 1-3 3-3ZM10 7c0-2 1-4 3-5M11 8c2-2 4-2 6-1"></path>
        <path *ngSwitchCase="'steps'" d="M5 4h14v16H5zM8 8h8M8 12h8M8 16h5"></path>
        <path *ngSwitchCase="'idea'" d="M9 18h6M10 22h4M8 14a7 7 0 1 1 8 0c-1 1-1 2-1 3H9c0-1 0-2-1-3Z"></path>
        <ng-container *ngSwitchCase="'cart'">
          <path d="M7 9V7a5 5 0 0 1 10 0v2M5 9h14l-1 11H6L5 9Z"></path>
        </ng-container>
        <ng-container *ngSwitchCase="'list'">
          <path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"></path>
        </ng-container>
      </ng-container>
    </svg>
  `,
  styles: [`
    :host { display: inline-flex; width: 1em; height: 1em; line-height: 1; }
    svg { width: 100%; height: 100%; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
  `]
})
export class UiIconComponent {
  @Input({ required: true }) name!: UiIconName;
}
