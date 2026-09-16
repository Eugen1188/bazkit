import { TestBed } from '@angular/core/testing';

import { appTestProviders } from '../test-providers';
import { SavedList, SavedListService } from './saved-list.service';


describe('SavedListService offline changes', () => {
  let service: SavedListService;

  beforeEach(() => {
    localStorage.clear();
    const payload = btoa(JSON.stringify({ user_id: 42 }))
      .replace(/=/g, '')
      .replace(/\+/g, '-')
      .replace(/\//g, '_');
    localStorage.setItem('access_token', `header.${payload}.signature`);
    TestBed.configureTestingModule({ providers: appTestProviders() });
    service = TestBed.inject(SavedListService);
  });

  afterEach(() => localStorage.clear());

  it('keeps only the latest offline state for one item', () => {
    service.queueSavedListToggle(7, 11, true);
    service.queueSavedListToggle(7, 11, false);

    const pending = service.getPendingToggles(7);
    expect(pending.length).toBe(1);
    expect(pending[0].isChecked).toBeFalse();
  });

  it('applies queued states to a freshly loaded list', () => {
    service.queueSavedListToggle(7, 11, true);
    const list = {
      id: 7,
      title: 'Gemeinsam',
      created_at: '',
      updated_at: '',
      item_count: 1,
      checked_count: 0,
      member_count: 2,
      access_role: 'editor',
      can_edit: true,
      is_owner: false,
      owner_name: 'Olivia',
      items: [{ id: 11, name: 'Milch', quantity: 1, unit: 'Liter', is_checked: false }]
    } satisfies SavedList;

    service.applyPendingToggles(list);

    expect(list.items[0].is_checked).toBeTrue();
  });

  it('removes a toggle after successful synchronization', () => {
    service.queueSavedListToggle(7, 11, true);
    service.removePendingToggle(7, 11);

    expect(service.getPendingToggles(7)).toEqual([]);
  });
});
