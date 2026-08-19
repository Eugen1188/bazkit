import {
  Injectable
} from '@angular/core';

import {
  HttpClient,
  HttpParams
} from '@angular/common/http';

import {
  Observable
} from 'rxjs';


export interface ProductSuggestion {

  id: number;

  name: string;

  category: string;

  default_unit: string;
}


@Injectable({
  providedIn: 'root'
})
export class ProductService {

  private apiUrl =
    this.getApiUrl();


  constructor(
    private http:
      HttpClient
  ) {}


  private getApiUrl():
    string {

    const hostname =
      window.location.hostname;


    const isLocal =
      hostname === 'localhost'
      ||
      hostname === '127.0.0.1';


    if (
      isLocal
    ) {

      return (
        'http://localhost:8000/products/'
      );
    }


    return (
      'http://178.104.47.231:8000/products/'
    );
  }


  searchProducts(
    query: string
  ): Observable<
    ProductSuggestion[]
  > {

    const params =
      new HttpParams()
        .set(
          'q',
          query
        );


    return this.http.get<
      ProductSuggestion[]
    >(
      `${this.apiUrl}search/`,
      {
        params
      }
    );
  }


  searchExternalProducts(
    query: string
  ): Observable<
    ProductSuggestion[]
  > {

    const params =
      new HttpParams()
        .set(
          'q',
          query
        );


    return this.http.get<
      ProductSuggestion[]
    >(
      `${this.apiUrl}external-search/`,
      {
        params
      }
    );
  }
}