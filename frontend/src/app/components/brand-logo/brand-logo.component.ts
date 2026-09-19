import { Component } from '@angular/core';


@Component({
  selector: 'app-brand-logo',
  standalone: true,
  template: `
    <span class="brand-logo">
      <svg class="brand-logo__icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 9V7a5 5 0 0 1 10 0v2"></path>
        <path d="M5 9h14l-1 11H6L5 9Z"></path>
        <path d="M15.2 13.2 14.8 17"></path>
      </svg>
      <span class="brand-logo__word" aria-label="bazkit">
        <span class="brand-logo__base">baz</span><span class="brand-logo__accent">kit</span>
      </span>
    </span>
  `,
  styles: [`
    :host {
      display: inline-flex;
      line-height: 1;
    }

    .brand-logo {
      display: inline-flex;
      align-items: center;
      gap: var(--brand-logo-gap, 0.38em);
      white-space: nowrap;
    }

    .brand-logo__icon {
      width: var(--brand-logo-icon-size, 1.1em);
      height: var(--brand-logo-icon-size, 1.1em);
      flex: 0 0 auto;
      fill: none;
      stroke: var(--color-primary);
      stroke-width: 1.8;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    .brand-logo__word {
      font-size: var(--brand-logo-word-size, 2rem);
      font-weight: 800;
      letter-spacing: -0.05em;
    }

    .brand-logo__base {
      color: var(--color-text-primary);
    }

    .brand-logo__accent {
      color: var(--color-primary);
    }
  `],
})
export class BrandLogoComponent {}
