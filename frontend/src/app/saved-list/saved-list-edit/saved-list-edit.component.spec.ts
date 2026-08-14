import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SavedListEditComponent } from './saved-list-edit.component';

describe('SavedListEditComponent', () => {
  let component: SavedListEditComponent;
  let fixture: ComponentFixture<SavedListEditComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SavedListEditComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SavedListEditComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
