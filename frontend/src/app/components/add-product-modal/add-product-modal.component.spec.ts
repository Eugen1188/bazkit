import { ComponentFixture, TestBed } from '@angular/core/testing';

import { appTestProviders } from '../../test-providers';
import { AddProductModalComponent } from './add-product-modal.component';

describe('AddProductModalComponent', () => {
  let component: AddProductModalComponent;
  let fixture: ComponentFixture<AddProductModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddProductModalComponent],
      providers: appTestProviders()
    })
    .compileComponents();

    fixture = TestBed.createComponent(AddProductModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
