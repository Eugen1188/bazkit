import { HttpClient } from '@angular/common/http';
import { of } from 'rxjs';

import { ShoppingList, ShoppingListService } from './shopping-list.service';
import { WeeklyPlannerService, WeeklyShoppingListResponse } from './weekly-planner.service';


describe('WeeklyPlannerService', () => {
  it('synchronizes the shopping-list cache after creating a weekly list', () => {
    const shoppingList: ShoppingList = {
      id: 1,
      title: 'Meine Einkaufsliste',
      created_at: '2026-09-08T00:00:00Z',
      updated_at: '2026-09-08T00:00:00Z',
      item_count: 1,
      completed_count: 0,
      items: [{
        id: 7,
        name: 'Kartoffel',
        quantity: 400,
        unit: 'g',
        note: 'Wochenplan 07.09.–13.09.2026',
        is_checked: false
      }]
    };
    const response: WeeklyShoppingListResponse = {
      shopping_list: shoppingList,
      meal_count: 1,
      ingredient_count: 1,
      product_count: 1,
      message: '1 Produkt wurde zur Einkaufsliste hinzugefügt.'
    };
    const http = jasmine.createSpyObj<HttpClient>('HttpClient', ['get', 'post']);
    const shoppingListService = new ShoppingListService(http);
    http.post.and.returnValue(of(response));
    const service = new WeeklyPlannerService(http, shoppingListService);

    service.createShoppingList('2026-09-07', '2026-09-13').subscribe();

    shoppingListService.getShoppingList().subscribe(cachedList => {
      expect(cachedList).toBe(shoppingList);
    });
    expect(http.get).not.toHaveBeenCalled();
  });
});
