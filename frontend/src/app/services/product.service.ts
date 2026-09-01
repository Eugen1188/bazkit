import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import {
  catchError,
  distinctUntilChanged,
  map,
  Observable,
  of,
  switchMap,
  timer,
  timeout
} from 'rxjs';

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
  grams_per_ml?: string | null;
  package_quantity?: string | null;
  package_unit?: string;
  unit_conversions?: ProductUnitConversion[];
  available_units?: string[];
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

export interface ProductSearchResult {
  products: ProductSuggestion[];
  unavailable: boolean;
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

@Injectable({ providedIn: 'root' })
export class ProductService {
  private readonly apiUrl = this.getApiUrl();
  private readonly searchCache = new Map<string, ProductSuggestion[]>();

  constructor(private readonly http: HttpClient) {}

  private getApiUrl(): string {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000/products/';
    }
    return 'http://178.104.47.231:8000/products/';
  }

  searchProducts(query: string, recipeOnly = false): Observable<ProductSuggestion[]> {
    return this.searchProductResults(query, recipeOnly).pipe(
      map(result => result.products),
      distinctUntilChanged((left, right) => (
        left.length === right.length
        && left.every((product, index) => (
          product.id === right[index]?.id
          && product.source === right[index]?.source
          && product.external_id === right[index]?.external_id
        ))
      )),
    );
  }

  searchProductResults(query: string, recipeOnly = false): Observable<ProductSearchResult> {
    const q = query.trim();
    if (q.length < 2) return of({ products: [], unavailable: false });
    const cachedProducts = this.cachedSuggestions(q, recipeOnly);
    if (cachedProducts.length > 0) {
      return of({ products: cachedProducts, unavailable: false });
    }
    let params = new HttpParams().set('q', q);
    if (recipeOnly) params = params.set('recipe_only', '1');
    const local$ = this.http.get<ProductSuggestion[]>(`${this.apiUrl}search/`, { params }).pipe(
      timeout({ first: 3500 }),
      map(products => ({ available: true, products })),
      catchError(() => of({ available: false, products: [] as ProductSuggestion[] })),
    );

    return local$.pipe(
      switchMap(local => {
        const localProducts = this.mergeProductSuggestions(local.products, [], recipeOnly);
        if (!local.available) {
          return of({ products: [], unavailable: true });
        }
        if (localProducts.length > 0) {
          this.rememberSuggestions(q, recipeOnly, localProducts);
          return of({ products: localProducts, unavailable: false });
        }
        const externalMinimumLength = recipeOnly ? 6 : 4;
        if (q.length < externalMinimumLength) {
          return of({ products: [], unavailable: false });
        }

        // Externe Quellen sind nur ein Fallback. Die kurze Ruhezeit verhindert,
        // dass für Zwischenstände beim Tippen teure OFF-/USDA-Anfragen starten.
        return timer(500).pipe(
          switchMap(() => this.http.get<ProductSuggestion[]>(`${this.apiUrl}external-search/`, { params }).pipe(
            timeout({ first: 4000 }),
            catchError(() => of([] as ProductSuggestion[])),
          )),
          map(external => {
            const products = this.mergeProductSuggestions([], external, recipeOnly);
            if (products.length > 0) this.rememberSuggestions(q, recipeOnly, products);
            return { products, unavailable: false };
          }),
        );
      }),
    );
  }

  private cachedSuggestions(query: string, recipeOnly: boolean): ProductSuggestion[] {
    const normalizedQuery = this.normalizeSearchText(query);
    const modePrefix = `${recipeOnly ? 'recipe' : 'all'}:`;
    const exact = this.searchCache.get(`${modePrefix}${normalizedQuery}`);
    if (exact?.length) return exact;

    const matchingPrefixes = [...this.searchCache.entries()]
      .filter(([key]) => key.startsWith(modePrefix))
      .map(([key, products]) => ({
        query: key.slice(modePrefix.length),
        products,
      }))
      .filter(entry => normalizedQuery.startsWith(entry.query))
      .sort((left, right) => right.query.length - left.query.length);
    for (const entry of matchingPrefixes) {
      const filtered = entry.products.filter(product => (
        this.normalizeSearchText(product.name).includes(normalizedQuery)
        || this.normalizeSearchText(product.canonical_name || '').includes(normalizedQuery)
      ));
      if (filtered.length > 0) return filtered;
    }
    return [];
  }

  private rememberSuggestions(
    query: string,
    recipeOnly: boolean,
    products: ProductSuggestion[],
  ): void {
    const key = `${recipeOnly ? 'recipe' : 'all'}:${this.normalizeSearchText(query)}`;
    this.searchCache.set(key, products);
    if (this.searchCache.size > 100) {
      const oldestKey = this.searchCache.keys().next().value;
      if (oldestKey) this.searchCache.delete(oldestKey);
    }
  }

  private normalizeSearchText(value: string): string {
    return value
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim()
      .toLocaleLowerCase('de-DE');
  }

  private mergeProductSuggestions(
    local: ProductSuggestion[],
    external: ProductSuggestion[],
    recipeOnly: boolean,
  ): ProductSuggestion[] {
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
