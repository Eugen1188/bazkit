import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GenerateRecipeComponent } from './generate-recipe.component';

describe('GenerateRecipeComponent', () => {
  let component: GenerateRecipeComponent;
  let fixture: ComponentFixture<GenerateRecipeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GenerateRecipeComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GenerateRecipeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
