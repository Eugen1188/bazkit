import { CommonModule } from '@angular/common';
import {
  Component,
  EventEmitter,
  forwardRef,
  Input,
  Output,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';


@Component({
  selector: 'app-ui-quantity-input',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ui-quantity-input.component.html',
  styleUrl: './ui-quantity-input.component.scss',
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => UiQuantityInputComponent),
    multi: true,
  }],
})
export class UiQuantityInputComponent implements ControlValueAccessor {
  @Input() inputId = '';
  @Input() min = 0.01;
  @Input() step = 1;
  @Input() ariaLabel = 'Menge';
  @Output() enterPressed = new EventEmitter<void>();

  value: number | null = 1;
  disabled = false;

  private onChange: (value: number | null) => void = () => undefined;
  private onTouched: () => void = () => undefined;

  writeValue(value: number | null): void {
    this.value = value === null || value === undefined ? null : Number(value);
  }

  registerOnChange(fn: (value: number | null) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(disabled: boolean): void {
    this.disabled = disabled;
  }

  selectValue(event: FocusEvent): void {
    (event.currentTarget as HTMLInputElement).select();
  }

  updateValue(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    const parsed = input.value === '' ? null : Number(input.value);
    this.setValue(parsed !== null && Number.isFinite(parsed) ? parsed : null);
  }

  adjust(direction: 1 | -1, event?: Event): void {
    event?.preventDefault();
    if (this.disabled) return;
    const current = Number.isFinite(Number(this.value)) ? Number(this.value) : 0;
    const next = Math.max(this.min, current + direction * this.step);
    this.setValue(Math.round(next * 100) / 100);
  }

  handleEnter(event: Event): void {
    event.preventDefault();
    this.enterPressed.emit();
  }

  markTouched(): void {
    this.onTouched();
  }

  private setValue(value: number | null): void {
    this.value = value;
    this.onChange(value);
    this.onTouched();
  }
}
