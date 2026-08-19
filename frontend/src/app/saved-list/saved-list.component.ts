import {
  CommonModule
} from '@angular/common';

import {
  Component,
  HostListener,
  OnInit
} from '@angular/core';

import {
  Router,
  RouterModule
} from '@angular/router';

import {
  SavedList,
  SavedListService
} from '../services/saved-list.service';

import {
  ListShareService
} from '../services/list-share.service';


@Component({
  selector: 'app-saved-list',

  standalone: true,

  imports: [
    CommonModule,
    RouterModule
  ],

  templateUrl:
    './saved-list.component.html',

  styleUrl:
    './saved-list.component.scss'
})
export class SavedListComponent
implements OnInit {

  savedLists:
    SavedList[] = [];

  isLoading = true;

  errorMessage = '';

  shareMessage = '';

  openedMenuId:
    number | null = null;


  constructor(
    private savedListService:
      SavedListService,

    private router:
      Router,

    private listShareService:
      ListShareService
  ) {}


  ngOnInit(): void {

    this.loadSavedLists();
  }


  loadSavedLists(): void {

    this.isLoading =
      true;

    this.errorMessage =
      '';


    this.savedListService
      .getSavedLists()
      .subscribe({

        next: (
          lists
        ) => {

          this.savedLists =
            lists;

          this.isLoading =
            false;
        },


        error: (
          error
        ) => {

          console.error(
            'Fehler beim Laden der Listen:',
            error
          );

          this.errorMessage =
            'Die Listen konnten nicht geladen werden.';

          this.isLoading =
            false;
        }

      });
  }


  toggleMenu(
    event: MouseEvent,
    listId: number
  ): void {

    event.preventDefault();

    event.stopPropagation();


    this.openedMenuId =
      this.openedMenuId === listId
        ? null
        : listId;
  }


  @HostListener(
    'document:click'
  )
  closeMenu(): void {

    this.openedMenuId =
      null;
  }


  editList(
    event: MouseEvent,
    list: SavedList
  ): void {

    event.preventDefault();

    event.stopPropagation();

    this.openedMenuId =
      null;


    this.router.navigate([
      '/main/saved-list',
      list.id,
      'edit'
    ]);
  }


  async shareList(
    event: MouseEvent,
    list: SavedList
  ): Promise<void> {

    event.preventDefault();

    event.stopPropagation();

    this.openedMenuId =
      null;

    this.shareMessage =
      '';


    try {

      let completeList =
        list;


      /*
       * Falls die Übersicht nur item_count
       * und keine vollständigen items enthält,
       * laden wir die Detailansicht nach.
       */
      if (
        !list.items
      ) {

        completeList =
          await new Promise<
            SavedList
          >(
            (
              resolve,
              reject
            ) => {

              this.savedListService
                .getSavedList(
                  list.id
                )
                .subscribe({

                  next:
                    resolve,

                  error:
                    reject

                });

            }
          );
      }


      const result =
        await this.listShareService
          .shareList(
            completeList.title,
            (
              completeList.items ??
              []
            ).map(
              item => ({
                name:
                  item.name ||
                  item.product_name ||
                  '',

                quantity:
                  item.quantity,

                unit:
                  item.unit,

                note:
                  item.note,

                isChecked:
                  false
              })
            )
          );


      if (
        result === 'copied'
      ) {

        this.showShareMessage(
          'Liste wurde in die Zwischenablage kopiert.'
        );
      }

    } catch (
      error
    ) {

      console.error(
        'Liste konnte nicht geteilt werden:',
        error
      );

      this.showShareMessage(
        'Die Liste konnte nicht geteilt werden.'
      );
    }
  }


  deleteList(
    event: MouseEvent,
    list: SavedList
  ): void {

    event.preventDefault();

    event.stopPropagation();

    this.openedMenuId =
      null;


    const shouldDelete =
      confirm(
        `Möchtest du "${list.title}" wirklich löschen?`
      );


    if (
      !shouldDelete
    ) {
      return;
    }


    this.savedListService
      .deleteSavedList(
        list.id
      )
      .subscribe({

        next: () => {

          this.savedLists =
            this.savedLists.filter(
              item =>
                item.id !==
                list.id
            );
        },


        error: (
          error
        ) => {

          console.error(
            'Liste konnte nicht gelöscht werden:',
            error
          );
        }

      });
  }


  private showShareMessage(
    message: string
  ): void {

    this.shareMessage =
      message;


    window.setTimeout(
      () => {

        if (
          this.shareMessage ===
          message
        ) {

          this.shareMessage =
            '';
        }

      },
      3000
    );
  }


  formatDate(
    date: string
  ): string {

    return new Intl.DateTimeFormat(
      'de-DE',
      {
        day:
          '2-digit',

        month:
          '2-digit',

        year:
          'numeric'
      }
    ).format(
      new Date(
        date
      )
    );
  }
}