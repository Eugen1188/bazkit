import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateSavedListModalComponent } from './create-saved-list-modal.component';

describe('CreateSavedListModalComponent', () => {
  let component: CreateSavedListModalComponent;
  let fixture: ComponentFixture<CreateSavedListModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CreateSavedListModalComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CreateSavedListModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
