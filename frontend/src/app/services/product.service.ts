import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { catchError, forkJoin, map, Observable, of } from 'rxjs';

export type ProductOrigin = 'local' | 'bls' | 'open_food_facts' | 'usda';
export type IngredientSearchContext = 'recipe_create' | 'recipe_edit' | 'shopping_list' | 'saved_list';

export interface ProductSuggestion {
  id: number | null;
  name: string;
  canonical_name?: string;
  is_recipe_ingredient?: boolean;
  category: string;
  shopping_category?: string;
  is_common_pantry?: boolean;
  brand: string;
  source: string | null;
  external_id: string | null;
  default_unit: string;
  grams_per_unit?: string | null;
  package_quantity?: string | null;
  package_unit?: string;
  unit_conversions?: ProductUnitConversion[];
  calories_per_100g: string | null;
  protein_per_100g: string | null;
  carbohydrates_per_100g: string | null;
  fat_per_100g: string | null;
  fiber_per_100g: string | null;
  nutrition_complete?: boolean;
  origin: ProductOrigin;
}

export interface ProductUnitConversion {
  unit: string;
  grams_per_unit: string;
  source: string;
  confidence: 'verified' | 'reference';
}

export interface PriceSnapshot {
  estimated_price?: number | null;
  price_source?: string;
  price_currency?: string;
  price_date?: string | null;
  price_store?: string;
  price_sample_count?: number;
  price_min?: number | null;
  price_max?: number | null;
  package_price?: number | null;
  package_quantity?: number | null;
  package_unit?: string;
}

export interface PriceEstimate extends PriceSnapshot {
  available: boolean;
  confidence: 'low' | 'medium' | 'high' | null;
  message: string;
}

@Injectable({ providedIn: 'root' })
export class ProductService {
  private readonly apiUrl = this.getApiUrl();

  constructor(private readonly http: HttpClient) {}

  private getApiUrl(): string {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000/products/';
    }
    return 'http://178.104.47.231:8000/products/';
  }

  searchProducts(query: string, recipeOnly = false): Observable<ProductSuggestion[]> {
    const q = query.trim();
    if (q.length < 2) return of([]);
    let params = new HttpParams().set('q', q);
    if (recipeOnly) params = params.set('recipe_only', '1');
    const local$ = this.http.get<ProductSuggestion[]>(`${this.apiUrl}search/`, { params })
      .pipe(catchError(() => of([] as ProductSuggestion[])));
    const external$ = q.length >= 4
      ? this.http.get<ProductSuggestion[]>(`${this.apiUrl}external-search/`, { params })
          .pipe(catchError(() => of([] as ProductSuggestion[])))
      : of([] as ProductSuggestion[]);

    return forkJoin([local$, external$]).pipe(map(([local, external]) => {
      const seen = new Set<string>();
      return [...local, ...external].filter(product => {
        if (recipeOnly && product.nutrition_complete === false) return false;
        const ingredientName = (product.canonical_name || product.name)
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .trim()
          .toLocaleLowerCase('de-DE');
        const key = recipeOnly
          ? `ingredient:${ingredientName}`
          : product.id !== null
            ? `id:${product.id}`
            : `${product.source}:${product.external_id}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      }).slice(0, 20);
    }));
  }

  persistExternalProduct(product: ProductSuggestion): Observable<ProductSuggestion> {
    if (product.id !== null) return of(product);
    return this.http.post<ProductSuggestion>(`${this.apiUrl}save-external/`, {
      source: product.source,
      external_id: product.external_id,
    });
  }

  recordIngredientSearch(
    query: string,
    resultCount: number,
    context: IngredientSearchContext,
  ): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}search-feedback/`, {
      query: query.trim(),
      context,
      event: 'search',
      result_count: resultCount,
    }).pipe(catchError(() => of(void 0)));
  }

  recordIngredientSelection(
    query: string,
    productId: number,
    selectedRank: number,
    context: IngredientSearchContext,
  ): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}search-feedback/`, {
      query: query.trim(),
      context,
      event: 'selected',
      product_id: productId,
      selected_rank: selectedRank,
    }).pipe(catchError(() => of(void 0)));
  }

  estimatePrice(
    product: ProductSuggestion,
    quantity: number | null,
    unit: string,
    mode: 'consumption' | 'purchase' = 'purchase',
  ): Observable<PriceEstimate> {
    let params = new HttpParams()
      .set('quantity', String(quantity ?? 1))
      .set('unit', unit || '')
      .set('mode', mode)
      .set('product_name', product.name);
    params = product.id !== null
      ? params.set('product_id', String(product.id))
      : params.set('source', product.source ?? '').set('external_id', product.external_id ?? '');
    return this.http.get<PriceEstimate>(`${this.apiUrl}price-estimate/`, { params });
  }

  searchExternalProducts(query: string): Observable<ProductSuggestion[]> {
    const q = query.trim();
    if (q.length < 4) return of([]);
    const params = new HttpParams().set('q', q);
    return this.http.get<ProductSuggestion[]>(`${this.apiUrl}external-search/`, { params });
  }

  saveExternalProduct(product: ProductSuggestion): Observable<ProductSuggestion> {
    if (product.id !== null) return of(product);
    return this.http.post<ProductSuggestion>(`${this.apiUrl}save-external/`, {
      source: product.source,
      external_id: product.external_id,
    });
  }
}
