import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddRecipeIngredientsModalComponent } from './add-recipe-ingredients-modal.component';

describe('AddRecipeIngredientsModalComponent', () => {
  let component: AddRecipeIngredientsModalComponent;
  let fixture: ComponentFixture<AddRecipeIngredientsModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddRecipeIngredientsModalComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AddRecipeIngredientsModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
