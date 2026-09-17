import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UiQuantityInputComponent } from './ui-quantity-input.component';


describe('UiQuantityInputComponent', () => {
  let component: UiQuantityInputComponent;
  let fixture: ComponentFixture<UiQuantityInputComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UiQuantityInputComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(UiQuantityInputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('changes the value in full steps and respects the minimum', () => {
    component.writeValue(3.98);
    component.adjust(1);
    expect(component.value).toBe(4.98);

    component.writeValue(0.5);
    component.adjust(-1);
    expect(component.value).toBe(0.01);
  });

  it('selects the complete value on focus', () => {
    const input = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    const selectSpy = spyOn(input, 'select');
    input.dispatchEvent(new FocusEvent('focus'));
    expect(selectSpy).toHaveBeenCalled();
  });
});
