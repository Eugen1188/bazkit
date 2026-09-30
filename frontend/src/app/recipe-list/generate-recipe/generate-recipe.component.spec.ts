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

  it('shows a useful message when the proxy times out', () => {
    const message = (component as any).apiError(
      { status: 504, error: '<html>Gateway Timeout</html>' },
      'Fallback',
    );

    expect(message).toBe(
      'Die Rezeptgenerierung hat zu lange gedauert. Bitte versuche es erneut.',
    );
  });

  it('renders a generated recipe including nutrition, ingredients and steps', () => {
    component.generatedRecipe = {
      name: 'Paprika-Gulasch',
      description: 'Herzhaft und aromatisch.',
      servings: 6,
      preparation_time: 150,
      category: 'lunch',
      ingredients: [
        {
          product: 1,
          product_detail: null,
          name: 'Rindergulasch',
          quantity: 900,
          unit: 'g',
        },
        {
          product: 2,
          product_detail: null,
          name: 'Paprika',
          quantity: 3,
          unit: 'Stück',
        },
      ],
      steps: [
        'Das Fleisch kräftig anbraten.',
        'Paprika hinzugeben und schmoren.',
      ],
      notes: 'Am besten heiß servieren.',
      nutrition: {
        calories: 487.35,
        protein: 42.16,
        carbohydrates: 18.4,
        fat: 24.81,
        fiber: 4.25,
      },
      nutrition_complete: true,
      nutrition_source: 'Geprüfter Produktkatalog',
    };

    expect(() => fixture.detectChanges()).not.toThrow();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Paprika-Gulasch');
    expect(text).toContain('487');
    expect(text).toContain('42,2');
    expect(text).toContain('Rindergulasch');
    expect(text).toContain('Paprika hinzugeben und schmoren.');
  });
});
