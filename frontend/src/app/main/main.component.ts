import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  ElementRef,
  OnDestroy
} from '@angular/core';

import {
  RouterOutlet
} from '@angular/router';

import {
  SidebarComponent
} from '../sidebar/sidebar.component';

import { CommunityService } from '../services/community.service';
import { RecipeService } from '../services/recipe.service';
import { SavedListService } from '../services/saved-list.service';
import { ShoppingListService } from '../services/shopping-list.service';
import { WeeklyPlannerService } from '../services/weekly-planner.service';


@Component({
  selector: 'app-main',

  standalone: true,

  imports: [
    SidebarComponent,
    RouterOutlet
  ],

  templateUrl:
    './main.component.html',

  styleUrl:
    './main.component.scss'
})
export class MainComponent implements AfterViewInit, OnDestroy {

  hasOpenModal = false;

  private readonly prefetchTimer: number;

  private modalObserver?: MutationObserver;


  constructor(
    private readonly shoppingListService: ShoppingListService,
    private readonly recipeService: RecipeService,
    private readonly savedListService: SavedListService,
    private readonly weeklyPlannerService: WeeklyPlannerService,
    private readonly communityService: CommunityService,
    private readonly hostElement: ElementRef<HTMLElement>,
    private readonly changeDetectorRef: ChangeDetectorRef
  ) {
    this.prefetchTimer = window.setTimeout(
      () => this.prefetchMainSections(),
      250
    );
  }


  ngAfterViewInit(): void {
    this.modalObserver = new MutationObserver(
      () => this.updateModalState()
    );

    this.modalObserver.observe(
      this.hostElement.nativeElement,
      {
        childList: true,
        subtree: true
      }
    );

    this.updateModalState();
  }


  ngOnDestroy(): void {
    window.clearTimeout(this.prefetchTimer);

    this.modalObserver?.disconnect();
  }


  private prefetchMainSections(): void {
    const ignorePrefetchError = { error: () => undefined };

    this.shoppingListService.getShoppingList().subscribe(ignorePrefetchError);
    this.recipeService.getRecipeSummaries().subscribe(ignorePrefetchError);
    this.savedListService.getSavedLists().subscribe(ignorePrefetchError);
    const { start, end } = this.currentWeekRange();
    this.weeklyPlannerService.getEntries(start, end).subscribe(ignorePrefetchError);
    this.communityService.getPosts().subscribe(ignorePrefetchError);
  }


  private updateModalState(): void {
    const nextState = this.hostElement.nativeElement.querySelector(
      '.modal-backdrop, .planner-dialog-backdrop, .edit-dialog-backdrop'
    ) !== null;

    if (nextState === this.hasOpenModal) {
      return;
    }

    this.hasOpenModal = nextState;
    this.changeDetectorRef.detectChanges();
  }


  private currentWeekRange(): { start: string; end: string } {
    const start = new Date();
    start.setHours(12, 0, 0, 0);
    start.setDate(start.getDate() - ((start.getDay() + 6) % 7));

    const end = new Date(start);
    end.setDate(start.getDate() + 6);

    return {
      start: this.dateKey(start),
      end: this.dateKey(end)
    };
  }


  private dateKey(value: Date): string {
    const month = String(value.getMonth() + 1).padStart(2, '0');
    const day = String(value.getDate()).padStart(2, '0');
    return `${value.getFullYear()}-${month}-${day}`;
  }

}
