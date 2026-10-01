import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';

import { PasswordResetComponent } from './password-reset.component';


describe('PasswordResetComponent', () => {
  let fixture: ComponentFixture<PasswordResetComponent>;
  let component: PasswordResetComponent;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PasswordResetComponent, HttpClientTestingModule],
      providers: [{
        provide: ActivatedRoute,
        useValue: {
          snapshot: {
            queryParamMap: { get: () => null },
          },
        },
      }],
    }).compileComponents();

    fixture = TestBed.createComponent(PasswordResetComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('requests a password reset without revealing account existence', () => {
    component.email = 'Test@Example.com';
    component.submit();

    const request = http.expectOne(request => request.url.endsWith('/users/password-reset/'));
    expect(request.request.body).toEqual({ email: 'test@example.com' });
    request.flush({ message: 'Falls ein Konto existiert, wurde ein Link versendet.' });

    expect(component.isComplete).toBeTrue();
  });
});
