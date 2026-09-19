import {
  APP_INITIALIZER,
  ApplicationConfig,
  ErrorHandler,
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
import {
  BazkitErrorHandler,
  BrowserErrorMonitorService,
  startBrowserErrorMonitoring,
} from './services/browser-error-monitor.service';


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

    {
      provide: ErrorHandler,
      useClass: BazkitErrorHandler,
    },

    {
      provide: APP_INITIALIZER,
      useFactory: startBrowserErrorMonitoring,
      deps: [BrowserErrorMonitorService],
      multi: true,
    },

  ]

};
