import { defineConfig, devices } from '@playwright/test';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';


const bundledPython = resolve(process.cwd(), '..', 'backend', '.venv', 'Scripts', 'python.exe');
const e2ePython = process.env['E2E_PYTHON']
  || (existsSync(bundledPython) ? `"${bundledPython}"` : 'python');


export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 90_000,
  expect: { timeout: 12_000 },
  retries: process.env['CI'] ? 1 : 0,
  reporter: process.env['CI'] ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: 'http://127.0.0.1:14200',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: `cd ../backend && ${e2ePython} manage.py migrate --noinput --settings=config.e2e_settings && ${e2ePython} manage.py e2e_setup reset --settings=config.e2e_settings && ${e2ePython} manage.py e2e_setup seed-product --settings=config.e2e_settings && ${e2ePython} -m uvicorn config.asgi:application --host 127.0.0.1 --port 18000`,
      url: 'http://127.0.0.1:18000/health/',
      env: { DJANGO_SETTINGS_MODULE: 'config.e2e_settings' },
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: 'npm run build && node scripts/serve-e2e.mjs',
      url: 'http://127.0.0.1:14200/',
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
