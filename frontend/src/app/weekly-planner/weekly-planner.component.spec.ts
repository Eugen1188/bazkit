import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { RecipeService } from '../services/recipe.service';
import { WeeklyPlannerService } from '../services/weekly-planner.service';
import { WeeklyPlannerComponent } from './weekly-planner.component';

describe('WeeklyPlannerComponent', () => {
  let component: WeeklyPlannerComponent;
  let fixture: ComponentFixture<WeeklyPlannerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WeeklyPlannerComponent],
      providers: [
        provideRouter([]),
        {
          provide: RecipeService,
          useValue: { getRecipes: () => of([]) }
        },
        {
          provide: WeeklyPlannerService,
          useValue: { getEntries: () => of([]) }
        }
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WeeklyPlannerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
