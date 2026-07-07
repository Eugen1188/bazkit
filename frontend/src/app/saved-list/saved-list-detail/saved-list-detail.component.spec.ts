import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SavedListDetailComponent } from './saved-list-detail.component';

describe('SavedListDetailComponent', () => {
  let component: SavedListDetailComponent;
  let fixture: ComponentFixture<SavedListDetailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SavedListDetailComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SavedListDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
