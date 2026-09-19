import { TestBed } from '@angular/core/testing';

import { BrowserErrorMonitorService } from './browser-error-monitor.service';


describe('BrowserErrorMonitorService', () => {
  let service: BrowserErrorMonitorService;
  let fetchSpy: jasmine.Spy;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(BrowserErrorMonitorService);
    fetchSpy = spyOn(window, 'fetch').and.returnValue(Promise.resolve(new Response(null)));
  });

  it('reports a browser error with the current route', () => {
    service.report(new TypeError('Kaputt'));

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [url, options] = fetchSpy.calls.mostRecent().args;
    const payload = JSON.parse((options as RequestInit).body as string);
    expect(url).toContain('/monitoring/browser-errors/');
    expect(payload.message).toBe('Kaputt');
    expect(payload.type).toBe('TypeError');
    expect(payload.path).toBe(window.location.pathname);
  });

  it('does not send the same error repeatedly within one minute', () => {
    service.report(new Error('Doppelt'));
    service.report(new Error('Doppelt'));

    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });
});
