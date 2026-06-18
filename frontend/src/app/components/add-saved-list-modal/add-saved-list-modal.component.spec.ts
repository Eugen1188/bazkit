import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddSavedListModalComponent } from './add-saved-list-modal.component';

describe('AddSavedListModalComponent', () => {
  let component: AddSavedListModalComponent;
  let fixture: ComponentFixture<AddSavedListModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddSavedListModalComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AddSavedListModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
