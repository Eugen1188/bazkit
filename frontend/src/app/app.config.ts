import {
  ApplicationConfig,
  isDevMode,
  provideZoneChangeDetection
} from '@angular/core';
import { provideServiceWorker } from '@angular/service-worker';

import {
  provideRouter
} from '@angular/router';

import {
  provideHttpClient,
  withInterceptors
} from '@angular/common/http';

import {
  routes
} from './app.routes';

import {
  authInterceptor
} from './interceptors/auth.interceptor';


export const appConfig: ApplicationConfig = {

  providers: [

    provideZoneChangeDetection({
      eventCoalescing: true
    }),

    provideRouter(routes),

    provideHttpClient(
      withInterceptors([
        authInterceptor
      ])
    ),

    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000'
    }),

  ]

};
