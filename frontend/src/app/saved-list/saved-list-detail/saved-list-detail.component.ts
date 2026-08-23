import {
  CommonModule
} from '@angular/common';

import {
  Component,
  HostListener,
  OnInit
} from '@angular/core';

import {
  ActivatedRoute,
  Router
} from '@angular/router';

import {
  SavedList,
  SavedListItem,
  SavedListService
} from '../../services/saved-list.service';

import {
  ListShareService
} from '../../services/list-share.service';


@Component({
  selector: 'app-saved-list-detail',

  standalone: true,

  imports: [
    CommonModule
  ],

  templateUrl:
    './saved-list-detail.component.html',

  styleUrl:
    './saved-list-detail.component.scss'
})
export class SavedListDetailComponent
implements OnInit {

  savedList:
    SavedList | null = null;


  isLoading = true;

  errorMessage = '';

  shareMessage = '';

  isMenuOpen = false;


  constructor(
    private route:
      ActivatedRoute,

    private router:
      Router,

    private savedListService:
      SavedListService,

    private listShareService:
      ListShareService
  ) {}


  ngOnInit(): void {

    this.loadSavedList();
  }


  loadSavedList(): void {

    const id =
      Number(
        this.route.snapshot
          .paramMap
          .get('id')
      );


    if (
      !id
    ) {

      this.errorMessage =
        'Die Liste konnte nicht gefunden werden.';

      this.isLoading =
        false;

      return;
    }


    this.isLoading =
      true;

    this.errorMessage =
      '';


    this.savedListService
      .getSavedList(
        id
      )
      .subscribe({

        next: (
          list
        ) => {

          this.savedList =
            list;

          this.isLoading =
            false;
        },


        error: (
          error
        ) => {

          console.error(
            'Liste konnte nicht geladen werden:',
            error
          );

          this.errorMessage =
            'Die Liste konnte nicht geladen werden.';

          this.isLoading =
            false;
        }

      });
  }


  toggleMenu(
    event: MouseEvent
  ): void {

    event.stopPropagation();

    this.isMenuOpen =
      !this.isMenuOpen;
  }


  @HostListener(
    'document:click'
  )
  closeMenu(): void {

    this.isMenuOpen =
      false;
  }


  editList(): void {

    if (
      !this.savedList
    ) {
      return;
    }


    this.isMenuOpen =
      false;


    this.router.navigate([
      '/main/saved-list',
      this.savedList.id,
      'edit'
    ]);
  }


  editItem(
    item: SavedListItem
  ): void {

    if (
      !this.savedList
    ) {
      return;
    }


    /*
     * Da du bereits eine komplette
     * Edit-Seite für die Liste hast,
     * öffnen wir diese auch beim
     * Bearbeiten eines einzelnen Produkts.
     */
    this.router.navigate([
      '/main/saved-list',
      this.savedList.id,
      'edit'
    ]);
  }


  async shareList(): Promise<void> {

    if (
      !this.savedList
    ) {
      return;
    }


    this.isMenuOpen =
      false;

    this.shareMessage =
      '';


    try {

      const result =
        await this.listShareService
          .shareList(
            this.savedList.title,
            (
              this.savedList.items ??
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


  deleteList(): void {

    if (
      !this.savedList
    ) {
      return;
    }


    this.isMenuOpen =
      false;


    const shouldDelete =
      confirm(
        `Möchtest du "${this.savedList.title}" wirklich löschen?`
      );


    if (
      !shouldDelete
    ) {
      return;
    }


    this.savedListService
      .deleteSavedList(
        this.savedList.id
      )
      .subscribe({

        next: () => {

          this.router.navigate([
            '/main/saved-list'
          ]);
        },


        error: (
          error
        ) => {

          console.error(
            'Liste konnte nicht gelöscht werden:',
            error
          );

          this.errorMessage =
            'Die Liste konnte nicht gelöscht werden.';
        }

      });
  }


  deleteItem(
    item: SavedListItem
  ): void {

    if (
      !this.savedList ||
      !item.id
    ) {
      return;
    }


    const shouldDelete =
      confirm(
        `Möchtest du "${this.getItemName(item)}" aus der Liste entfernen?`
      );


    if (
      !shouldDelete
    ) {
      return;
    }


    this.savedListService
      .deleteSavedListItem(
        this.savedList.id,
        item.id
      )
      .subscribe({

        next: () => {

          if (
            !this.savedList
          ) {
            return;
          }


          this.savedList.items =
            (
              this.savedList.items ??
              []
            )
              .filter(
                currentItem =>
                  currentItem.id !==
                  item.id
              );
        },


        error: (
          error
        ) => {

          console.error(
            'Produkt konnte nicht gelöscht werden:',
            error
          );
        }

      });
  }


  getItemName(
    item: SavedListItem
  ): string {

    return (
      item.name ||
      item.product_name ||
      'Produkt'
    );
  }


  get itemCount():
    number {

    return (
      this.savedList?.items?.length ??
      0
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
}