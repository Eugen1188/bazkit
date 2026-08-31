import {
  Component,
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
export class MainComponent implements OnDestroy {

  private readonly prefetchTimer: number;


  constructor(
    private readonly shoppingListService: ShoppingListService,
    private readonly recipeService: RecipeService,
    private readonly savedListService: SavedListService,
    private readonly weeklyPlannerService: WeeklyPlannerService,
    private readonly communityService: CommunityService
  ) {
    this.prefetchTimer = window.setTimeout(
      () => this.prefetchMainSections(),
      250
    );
  }


  ngOnDestroy(): void {
    window.clearTimeout(this.prefetchTimer);
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
