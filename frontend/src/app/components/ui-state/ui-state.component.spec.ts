import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UiStateComponent } from './ui-state.component';


describe('UiStateComponent', () => {
  let fixture: ComponentFixture<UiStateComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [UiStateComponent] }).compileComponents();
    fixture = TestBed.createComponent(UiStateComponent);
  });

  it('renders an accessible error state', () => {
    fixture.componentRef.setInput('kind', 'error');
    fixture.componentRef.setInput('title', 'Nicht erreichbar');
    fixture.componentRef.setInput('message', 'Bitte versuche es erneut.');
    fixture.detectChanges();

    const element = fixture.nativeElement.querySelector('section') as HTMLElement;
    expect(element.getAttribute('role')).toBe('alert');
    expect(element.textContent).toContain('Nicht erreichbar');
    expect(element.textContent).toContain('Bitte versuche es erneut.');
  });

  it('emits the action when the retry button is pressed', () => {
    fixture.componentRef.setInput('message', 'Fehler');
    fixture.componentRef.setInput('actionLabel', 'Erneut versuchen');
    const action = jasmine.createSpy('action');
    fixture.componentInstance.action.subscribe(action);
    fixture.detectChanges();

    (fixture.nativeElement.querySelector('button') as HTMLButtonElement).click();

    expect(action).toHaveBeenCalledTimes(1);
  });
});
