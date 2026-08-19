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
    'http://178.104.47.231:8000/products/';


  constructor(
    private http:
      HttpClient
  ) {}


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
}