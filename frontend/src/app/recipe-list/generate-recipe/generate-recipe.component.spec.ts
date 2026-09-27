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
});
