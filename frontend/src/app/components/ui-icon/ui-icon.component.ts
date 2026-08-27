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
  | 'list'
  | 'shopping-basket'
  | 'home'
  | 'shopping-cart'
  | 'chef-hat'
  | 'calendar-days'
  | 'clipboard-list'
  | 'users-round'
  | 'settings'
  | 'log-out'
  | 'chevron-down'
  | 'crown'
  | 'plus'
  | 'search'
  | 'heart'
  | 'message-circle'
  | 'star'
  | 'chevron-right'
  | 'x'
  | 'arrow-left'
  | 'book-open'
  | 'messages-square';


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
        <ng-container *ngSwitchCase="'shopping-basket'">
          <path d="M3 10h18M7 10V8a5 5 0 0 1 10 0v2M5 10l1.4 10h11.2L19 10M9 14v2M15 14v2"></path>
        </ng-container>
        <ng-container *ngSwitchCase="'home'">
          <path d="m3 11 9-8 9 8M5 10v11h14V10M9 21v-7h6v7"></path>
        </ng-container>
        <ng-container *ngSwitchCase="'shopping-cart'">
          <path d="M3 3h2l2.3 11.2a2 2 0 0 0 2 1.6h7.8a2 2 0 0 0 2-1.6L21 7H6"></path>
          <circle cx="10" cy="20" r="1"></circle><circle cx="18" cy="20" r="1"></circle>
        </ng-container>
        <ng-container *ngSwitchCase="'chef-hat'">
          <path d="M6 13.9A4 4 0 0 1 7.5 6.1a5 5 0 0 1 9 0 4 4 0 0 1 1.5 7.8V21H6v-7.1ZM6 17h12"></path>
        </ng-container>
        <ng-container *ngSwitchCase="'calendar-days'">
          <rect x="3" y="5" width="18" height="16" rx="2"></rect><path d="M16 3v4M8 3v4M3 10h18M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"></path>
        </ng-container>
        <ng-container *ngSwitchCase="'clipboard-list'">
          <rect x="5" y="4" width="14" height="17" rx="2"></rect><path d="M9 4.5V3h6v1.5M9 9h6M9 13h6M9 17h4"></path>
        </ng-container>
        <ng-container *ngSwitchCase="'users-round'">
          <circle cx="9" cy="8" r="3"></circle><circle cx="17" cy="9" r="2.5"></circle><path d="M3 20a6 6 0 0 1 12 0M14.5 15a5 5 0 0 1 6.5 5"></path>
        </ng-container>
        <ng-container *ngSwitchCase="'settings'">
          <circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"></path>
        </ng-container>
        <ng-container *ngSwitchCase="'log-out'">
          <path d="M10 17l5-5-5-5M15 12H3M21 4v16"></path>
        </ng-container>
        <path *ngSwitchCase="'chevron-down'" d="m6 9 6 6 6-6"></path>
        <ng-container *ngSwitchCase="'crown'">
          <path d="m3 6 4 5 5-7 5 7 4-5-2 13H5L3 6ZM5 22h14"></path>
        </ng-container>
        <path *ngSwitchCase="'plus'" d="M12 5v14M5 12h14"></path>
        <ng-container *ngSwitchCase="'search'">
          <circle cx="11" cy="11" r="7"></circle><path d="m20 20-4-4"></path>
        </ng-container>
        <path *ngSwitchCase="'heart'" d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8Z"></path>
        <path *ngSwitchCase="'message-circle'" d="M21 15a4 4 0 0 1-4 4H9l-5 3v-7a7 7 0 1 1 17 0Z"></path>
        <path *ngSwitchCase="'star'" d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9L12 3Z"></path>
        <path *ngSwitchCase="'chevron-right'" d="m9 18 6-6-6-6"></path>
        <path *ngSwitchCase="'x'" d="M6 6l12 12M18 6 6 18"></path>
        <path *ngSwitchCase="'arrow-left'" d="m15 18-6-6 6-6M9 12h10"></path>
        <ng-container *ngSwitchCase="'book-open'">
          <path d="M3 5a5 5 0 0 1 5-1l4 2v15l-4-2a5 5 0 0 0-5 1V5ZM21 5a5 5 0 0 0-5-1l-4 2v15l4-2a5 5 0 0 1 5 1V5Z"></path>
        </ng-container>
        <ng-container *ngSwitchCase="'messages-square'">
          <path d="M8 18H5l-3 3V7a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v3M10 15a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v7l-3-2h-6a3 3 0 0 1-3-3v-2Z"></path>
        </ng-container>
      </ng-container>
    </svg>
  `,
  styles: [`
    :host { display: inline-flex; width: 1em; height: 1em; line-height: 1; }
    svg { width: 100%; height: 100%; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
    :host(.filled) svg { fill: currentColor; }
  `]
})
export class UiIconComponent {
  @Input({ required: true }) name!: UiIconName;
}
