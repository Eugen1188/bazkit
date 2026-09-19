import { HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { API_ROOT, apiEndpoint } from '../config/api.config';
import { appTestProviders } from '../test-providers';
import { AuthService } from './auth.service';
import { RecipePayload, RecipeService } from './recipe.service';


describe('critical workflow service contracts', () => {
  let http: HttpTestingController;
  let auth: AuthService;
  let recipes: RecipeService;

  const recipePayload: RecipePayload = {
    name: 'Tomatensalat',
    description: 'Schnell',
    servings: 2,
    preparation_time: 10,
    category: 'lunch',
    instructions: '1. Schneiden',
    notes: '',
    image_position_x: 50,
    image_position_y: 50,
    image_zoom: 100,
    ingredients: [{
      product: 7,
      name: 'Tomate',
      quantity: 200,
      unit: 'g',
      note: 'gewürfelt',
    }],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: appTestProviders() });
    http = TestBed.inject(HttpTestingController);
    auth = TestBed.inject(AuthService);
    recipes = TestBed.inject(RecipeService);
  });

  afterEach(() => http.verify());

  it('registers an account and verifies its e-mail token', () => {
    const registration = {
      first_name: 'Eva', last_name: 'Beispiel', email: 'eva@example.com',
      password: 'Passwort123', password2: 'Passwort123', accept_terms: true,
    };

    auth.register(registration).subscribe();
    const registerRequest = http.expectOne(`${API_ROOT}/users/register/`);
    expect(registerRequest.request.method).toBe('POST');
    expect(registerRequest.request.body).toEqual(registration);
    registerRequest.flush({ verification_required: true });

    auth.verifyEmail('verification-token').subscribe();
    const verifyRequest = http.expectOne(`${API_ROOT}/users/verify-email/`);
    expect(verifyRequest.request.method).toBe('POST');
    expect(verifyRequest.request.body).toEqual({ token: 'verification-token' });
    verifyRequest.flush({ message: 'Bestätigt', email: registration.email });
  });

  it('creates and edits a recipe with the complete ingredient payload', () => {
    recipes.createRecipe(recipePayload).subscribe();
    const createRequest = http.expectOne(apiEndpoint('recipes/'));
    expect(createRequest.request.method).toBe('POST');
    expect(createRequest.request.body).toEqual(recipePayload);
    createRequest.flush({ id: 12, ...recipePayload });

    const edited = { ...recipePayload, name: 'Tomatensalat mit Kräutern' };
    recipes.updateRecipe(12, edited).subscribe();
    const editRequest = http.expectOne(apiEndpoint('recipes/12/'));
    expect(editRequest.request.method).toBe('PUT');
    expect(editRequest.request.body.name).toBe('Tomatensalat mit Kräutern');
    editRequest.flush({ id: 12, ...edited });
  });

  it('uploads an avatar and deletes the account through authenticated endpoints', () => {
    const avatar = new File(['avatar'], 'avatar.png', { type: 'image/png' });

    auth.uploadAvatar(avatar).subscribe();
    const uploadRequest = http.expectOne(`${API_ROOT}/users/me/avatar/`);
    expect(uploadRequest.request.method).toBe('PUT');
    expect(uploadRequest.request.body instanceof FormData).toBeTrue();
    expect((uploadRequest.request.body as FormData).get('avatar')).toBe(avatar);
    uploadRequest.flush({ id: 1, avatar_url: 'https://example.test/avatar.webp' });

    auth.deleteAccount().subscribe();
    const deleteRequest = http.expectOne(`${API_ROOT}/users/me/`);
    expect(deleteRequest.request.method).toBe('DELETE');
    deleteRequest.flush(null);
  });
});
