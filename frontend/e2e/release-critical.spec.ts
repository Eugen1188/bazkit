import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

import { expect, Page, test } from '@playwright/test';


const backendDirectory = resolve(process.cwd(), '..', 'backend');
const localPython = resolve(backendDirectory, '.venv', 'Scripts', 'python.exe');
const python = process.env['E2E_PYTHON'] || (
  process.platform === 'win32' && existsSync(localPython) ? localPython : 'python'
);
const apiBase = 'http://127.0.0.1:18000';
const defaultPassword = 'E2ePasswort123';

function setup(action: string, ...args: string[]): string {
  return execFileSync(
    python,
    ['manage.py', 'e2e_setup', action, ...args, '--settings=config.e2e_settings'],
    {
      cwd: backendDirectory,
      encoding: 'utf8',
      env: { ...process.env, DJANGO_SETTINGS_MODULE: 'config.e2e_settings' },
    },
  ).trim();
}

function createUser(email: string, firstName: string): void {
  setup(
    'create-user',
    '--email', email,
    '--password', defaultPassword,
    '--first-name', firstName,
    '--last-name', 'Test',
  );
}

async function login(page: Page, email: string, password = defaultPassword): Promise<void> {
  await page.goto('/login');
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole('button', { name: 'Login', exact: true }).click();
  await expect(page).toHaveURL(/\/main\/home/);
}

async function accessToken(page: Page): Promise<string> {
  return page.evaluate(() => localStorage.getItem('access_token') || '');
}

async function postApi(page: Page, path: string, data: object) {
  const token = await accessToken(page);
  const response = await page.request.post(`${apiBase}${path}`, {
    data,
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(response.ok(), `${path}: ${response.status()} ${await response.text()}`).toBeTruthy();
  return response.json();
}

async function createRecipeViaApi(page: Page, name = 'Kartoffelpfanne') {
  const productId = Number(setup('seed-product'));
  return postApi(page, '/recipes/', {
    name,
    description: 'Ein verlässliches Rezept für den Browser-Test.',
    servings: 2,
    preparation_time: 25,
    category: 'dinner',
    instructions: '1. Kartoffeln vorbereiten.\n2. Alles garen.',
    notes: '',
    image_position_x: 50,
    image_position_y: 50,
    image_zoom: 100,
    ingredients: [{ product: productId, name: 'Kartoffel', quantity: 500, unit: 'g', note: '' }],
  });
}

function currentMonday(): string {
  const now = new Date();
  const day = now.getDay() || 7;
  now.setDate(now.getDate() - day + 1);
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const date = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${date}`;
}

test.describe.configure({ mode: 'serial' });

test.beforeEach(() => {
  setup('reset');
  setup('seed-product');
});

test('registration, email confirmation and password reset work end to end', async ({ page }) => {
  const email = 'registration-e2e@example.com';
  await page.goto('/register');
  await page.locator('input[name="first_name"]').fill('Regina');
  await page.locator('input[name="last_name"]').fill('Test');
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(defaultPassword);
  await page.locator('input[name="password2"]').fill(defaultPassword);
  await page.locator('input[name="accept_terms"]').check();
  await page.getByRole('button', { name: 'Registrieren', exact: true }).click();
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByText('Bestätigungslink geschickt')).toBeVisible();

  await page.goto(setup('verification-url', '--email', email));
  await expect(page.getByRole('heading', { name: 'Bestätigung erfolgreich' })).toBeVisible();

  await page.goto('/passwort-zuruecksetzen');
  await page.locator('#resetEmail').fill(email);
  await page.getByRole('button', { name: 'Link anfordern' }).click();
  await expect(page.getByText(/Falls ein aktives Konto/)).toBeVisible();

  await page.goto(setup('password-reset-url', '--email', email));
  await page.locator('#newPassword').fill('NeuesE2ePasswort456');
  await page.locator('#repeatedPassword').fill('NeuesE2ePasswort456');
  await page.getByRole('button', { name: 'Passwort speichern' }).click();
  await expect(page.getByText('erfolgreich geändert')).toBeVisible();
  await login(page, email, 'NeuesE2ePasswort456');
});

test('a recipe can be created and edited through the browser', async ({ page }) => {
  const email = 'recipe-e2e@example.com';
  createUser(email, 'Rezept');
  await login(page, email);
  await page.goto('/main/recipe-list/create');

  await page.locator('#recipeName').fill('E2E Kartoffelgericht');
  await page.locator('#description').fill('Im Browser vollständig angelegt.');
  await page.locator('#servings').fill('2');
  await page.locator('#preparationTime').fill('25');
  await page.getByRole('button', { name: 'Weiter', exact: true }).click();

  await page.locator('#ingredientName0').fill('Kartoffel');
  await page.locator('.suggestion-option').filter({ hasText: 'Kartoffel' }).first().click();
  await page.locator('#ingredientAmount0').fill('500');
  await page.locator('#ingredientUnit0').selectOption('g');
  await page.getByRole('button', { name: 'Weiter', exact: true }).click();

  await page.locator('.preparation-item textarea').first().fill('Kartoffeln waschen, schneiden und garen.');
  await page.getByRole('button', { name: 'Weiter', exact: true }).click();
  await page.getByRole('button', { name: 'Rezept speichern' }).click();
  await expect(page.getByRole('heading', { name: 'E2E Kartoffelgericht' })).toBeVisible();

  await page.getByRole('button', { name: 'Rezept bearbeiten' }).click();
  await page.locator('#recipeName').fill('E2E Kartoffelgericht bearbeitet');
  await page.getByRole('button', { name: 'Weiter', exact: true }).click();
  await page.getByRole('button', { name: 'Weiter', exact: true }).click();
  await page.getByRole('button', { name: 'Weiter', exact: true }).click();
  await page.getByRole('button', { name: 'Änderungen speichern' }).click();
  await expect(page.getByRole('heading', { name: 'E2E Kartoffelgericht bearbeitet' })).toBeVisible();
});

test('the weekly plan is transferred to the shopping list', async ({ page }) => {
  const email = 'planner-e2e@example.com';
  createUser(email, 'Planer');
  await login(page, email);
  const recipe = await createRecipeViaApi(page);
  await postApi(page, '/planner/entries/', {
    date: currentMonday(),
    meal_type: 'dinner',
    servings: 2,
    recipe: recipe.id,
  });

  await page.goto('/main/weekly-planner');
  await expect(page.getByText('Kartoffelpfanne').first()).toBeVisible();
  await page.getByRole('button', { name: 'Zur Einkaufsliste hinzufügen' }).click();
  await expect(page).toHaveURL(/\/main\/shopping-list/);
  await expect(page.getByText('Kartoffel').first()).toBeVisible();
});

test('two users edit a shared list and offline changes synchronize', async ({ browser }) => {
  const ownerEmail = 'owner-e2e@example.com';
  const memberEmail = 'member-e2e@example.com';
  createUser(ownerEmail, 'Olivia');
  createUser(memberEmail, 'Milan');

  const ownerContext = await browser.newContext();
  const memberContext = await browser.newContext();
  const ownerPage = await ownerContext.newPage();
  const memberPage = await memberContext.newPage();
  await login(ownerPage, ownerEmail);
  const savedList = await postApi(ownerPage, '/lists/saved-lists/', {
    title: 'Gemeinsamer E2E Einkauf',
    items: [{ name: 'Hafermilch', quantity: 1, unit: 'Packung', note: '' }],
  });
  const invitation = await postApi(
    ownerPage,
    `/lists/saved-lists/${savedList.id}/collaboration/`,
    { email: memberEmail, role: 'editor' },
  );

  await login(memberPage, memberEmail);
  await memberPage.goto(invitation.invite_url.replace('localhost', '127.0.0.1'));
  await memberPage.getByRole('button', { name: 'Einladung annehmen' }).click();
  await expect(memberPage).toHaveURL(new RegExp(`/main/saved-list/${savedList.id}`));
  await ownerPage.goto(`/main/saved-list/${savedList.id}`);
  await expect(ownerPage.getByText('Hafermilch')).toBeVisible();
  await expect(memberPage.getByText('Hafermilch')).toBeVisible();

  await memberContext.setOffline(true);
  await memberPage.getByRole('checkbox', { name: /Hafermilch abhaken/ }).click();
  await expect(memberPage.getByText(/Offline gespeichert/)).toBeVisible();
  await memberContext.setOffline(false);
  await expect(ownerPage.getByText(/Abgehakt von Milan Test/)).toBeVisible({ timeout: 20_000 });

  await ownerContext.close();
  await memberContext.close();
});

test('a profile image can be uploaded and the account can be deleted', async ({ page }) => {
  const email = 'account-e2e@example.com';
  createUser(email, 'Konto');
  await login(page, email);
  await page.goto('/main/settings');
  await page.getByRole('button', { name: 'Profil bearbeiten' }).click();
  await page.locator('input[type="file"]').setInputFiles({
    name: 'avatar.png',
    mimeType: 'image/png',
    buffer: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=', 'base64'),
  });
  await page.getByRole('button', { name: 'Änderungen speichern' }).click();
  await expect(page.getByText('Profilbild und deine Angaben wurden aktualisiert')).toBeVisible();

  await page.getByRole('button', { name: /Konto dauerhaft löschen/ }).click();
  await page.locator('input[name="deleteConfirmation"]').fill('LÖSCHEN');
  await page.getByRole('button', { name: 'Konto endgültig löschen' }).click();
  await expect(page).toHaveURL('http://127.0.0.1:14200/');
  expect(setup('user-exists', '--email', email)).toBe('false');
});
