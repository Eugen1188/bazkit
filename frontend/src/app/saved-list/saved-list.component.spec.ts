import { ComponentFixture, TestBed } from '@angular/core/testing';

import { appTestProviders } from '../test-providers';
import { SavedListComponent } from './saved-list.component';

describe('SavedListComponent', () => {
  let component: SavedListComponent;
  let fixture: ComponentFixture<SavedListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SavedListComponent],
      providers: appTestProviders()
    })
    .compileComponents();

    fixture = TestBed.createComponent(SavedListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
