import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import {
  UiDialogDirective,
  UiNumberInputDirective,
} from './ui-primitives.directive';


@Component({
  standalone: true,
  imports: [UiDialogDirective, UiNumberInputDirective],
  template: `
    <section appUiDialog role="dialog"></section>
    <input appUiNumberInput type="number" step="1" value="3" />
  `,
})
class PrimitiveHostComponent {}


describe('UI primitives', () => {
  let fixture: ComponentFixture<PrimitiveHostComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PrimitiveHostComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(PrimitiveHostComponent);
    fixture.detectChanges();
  });

  it('applies the shared dialog class', () => {
    const dialog = fixture.nativeElement.querySelector('[role="dialog"]');
    expect(dialog.classList.contains('ui-dialog')).toBeTrue();
  });

  it('selects the complete number when the field receives focus', () => {
    const input: HTMLInputElement = fixture.nativeElement.querySelector('input');
    const selectSpy = spyOn(input, 'select');

    input.dispatchEvent(new FocusEvent('focus'));

    expect(selectSpy).toHaveBeenCalled();
  });
});
