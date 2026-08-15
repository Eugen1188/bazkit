import { inject } from '@angular/core';
import {
  HttpErrorResponse,
  HttpInterceptorFn
} from '@angular/common/http';
import { Router } from '@angular/router';
import {
  catchError,
  switchMap,
  throwError
} from 'rxjs';

import { AuthService } from '../services/auth.service';


export const authInterceptor: HttpInterceptorFn = (
  req,
  next
) => {

  const authService =
    inject(AuthService);

  const router =
    inject(Router);

  const accessToken =
    localStorage.getItem('access_token');

  const isAuthRequest =
    req.url.includes('/users/login/') ||
    req.url.includes('/users/register/') ||
    req.url.includes('/api/token/refresh/');

  let request = req;


  if (
    accessToken &&
    !isAuthRequest
  ) {

    request = req.clone({
      setHeaders: {
        Authorization:
          `Bearer ${accessToken}`
      }
    });

  }


  return next(request).pipe(

    catchError(
      (error: HttpErrorResponse) => {

        if (
          error.status !== 401 ||
          isAuthRequest
        ) {

          return throwError(
            () => error
          );

        }


        const refreshToken =
          localStorage.getItem(
            'refresh_token'
          );


        if (!refreshToken) {

          authService.logout();

          router.navigate(['/']);

          return throwError(
            () => error
          );

        }


        return authService
          .refreshToken()
          .pipe(

            switchMap(
              (response) => {

                const newAccessToken =
                  response.access;

                localStorage.setItem(
                  'access_token',
                  newAccessToken
                );


                const retryRequest =
                  req.clone({
                    setHeaders: {
                      Authorization:
                        `Bearer ${newAccessToken}`
                    }
                  });


                return next(
                  retryRequest
                );

              }
            ),

            catchError(
              (refreshError) => {

                authService.logout();

                router.navigate(['/']);

                return throwError(
                  () => refreshError
                );

              }
            )

          );

      }
    )

  );
};