import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { GenerateRecipeComponent } from './generate-recipe.component';

describe('GenerateRecipeComponent', () => {
  let component: GenerateRecipeComponent;
  let fixture: ComponentFixture<GenerateRecipeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GenerateRecipeComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
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
