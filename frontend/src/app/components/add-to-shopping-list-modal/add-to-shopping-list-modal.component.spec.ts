import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddToShoppingListModalComponent } from './add-to-shopping-list-modal.component';

describe('AddToShoppingListModalComponent', () => {
  let component: AddToShoppingListModalComponent;
  let fixture: ComponentFixture<AddToShoppingListModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddToShoppingListModalComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AddToShoppingListModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
