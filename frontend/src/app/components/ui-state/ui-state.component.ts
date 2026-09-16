import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';


export type UiStateKind = 'loading' | 'error' | 'empty';


@Component({
  selector: 'app-ui-state',
  standalone: true,
  imports: [CommonModule],
  template: `
    <section
      class="ui-state"
      [class.error]="kind === 'error'"
      [class.empty]="kind === 'empty'"
      [attr.role]="kind === 'error' ? 'alert' : 'status'"
      [attr.aria-live]="kind === 'error' ? 'assertive' : 'polite'"
    >
      <span class="spinner" *ngIf="kind === 'loading'" aria-hidden="true"></span>

      <span class="state-icon" *ngIf="kind === 'error'" aria-hidden="true">!</span>

      <div class="copy">
        <strong *ngIf="title">{{ title }}</strong>
        <p>{{ message }}</p>
      </div>

      <button type="button" *ngIf="actionLabel" (click)="action.emit()">
        {{ actionLabel }}
      </button>
    </section>
  `,
  styleUrl: './ui-state.component.scss'
})
export class UiStateComponent {
  @Input() kind: UiStateKind = 'loading';
  @Input() title = '';
  @Input({ required: true }) message = '';
  @Input() actionLabel = '';
  @Output() readonly action = new EventEmitter<void>();
}
