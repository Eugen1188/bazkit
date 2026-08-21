import {
  CommonModule
} from '@angular/common';

import {
  Component
} from '@angular/core';

import {
  FormsModule
} from '@angular/forms';


interface CommunityCategory {
  id:
    'recipe'
    | 'list'
    | 'thread';

  title:
    string;

  description:
    string;

  count:
    number;
}


interface CommunityPreview {
  type:
    'recipe'
    | 'list'
    | 'thread';

  title:
    string;

  author:
    string;

  time:
    string;

  meta:
    string;

  description:
    string;
}


@Component({
  selector:
    'app-community',

  standalone:
    true,

  imports: [
    CommonModule,
    FormsModule
  ],

  templateUrl:
    './community.component.html',

  styleUrl:
    './community.component.scss'
})
export class CommunityComponent {

  searchQuery =
    '';


  activeFilter:
    'all'
    | 'recipe'
    | 'list'
    | 'thread' =
      'all';


  categories:
    CommunityCategory[] = [

      {
        id:
          'recipe',

        title:
          'Rezepte',

        description:
          'Entdecke Rezepte aus der Community.',

        count:
          0
      },

      {
        id:
          'list',

        title:
          'Einkaufslisten',

        description:
          'Finde und übernimm geteilte Einkaufslisten.',

        count:
          0
      },

      {
        id:
          'thread',

        title:
          'Diskussionen',

        description:
          'Stelle Fragen und tausche dich mit anderen aus.',

        count:
          0
      }

    ];


  previews:
    CommunityPreview[] = [

      {
        type:
          'recipe',

        title:
          'Cremige Hähnchenpasta',

        author:
          'Anna',

        time:
          'vor 2 Std.',

        meta:
          '25 Min. · 4 Portionen',

        description:
          'Ein schnelles Pastagericht für den Feierabend.'
      },

      {
        type:
          'list',

        title:
          'Wocheneinkauf für 2 Personen',

        author:
          'Max',

        time:
          'vor 4 Std.',

        meta:
          '18 Produkte',

        description:
          'Eine einfache Einkaufsliste für eine ganze Woche.'
      },

      {
        type:
          'thread',

        title:
          'Welche Heißluftfritteuse könnt ihr empfehlen?',

        author:
          'Lisa',

        time:
          'vor 35 Min.',

        meta:
          '12 Antworten',

        description:
          'Ich suche eine gute Heißluftfritteuse für ungefähr 100 bis 150 Euro.'
      }

    ];


  setFilter(
    filter:
      'all'
      | 'recipe'
      | 'list'
      | 'thread'
  ): void {

    this.activeFilter =
      filter;
  }


  get filteredPreviews():
    CommunityPreview[] {

    const search =
      this.searchQuery
        .trim()
        .toLowerCase();


    return this.previews
      .filter(
        item => {

          if (
            this.activeFilter !==
              'all'
            &&
            item.type !==
              this.activeFilter
          ) {

            return false;
          }


          if (
            !search
          ) {

            return true;
          }


          return (
            item.title
              .toLowerCase()
              .includes(
                search
              )
            ||
            item.description
              .toLowerCase()
              .includes(
                search
              )
            ||
            item.author
              .toLowerCase()
              .includes(
                search
              )
          );
        }
      );
  }


  getTypeLabel(
    type:
      CommunityPreview['type']
  ): string {

    switch (
      type
    ) {

      case 'recipe':
        return 'Rezept';

      case 'list':
        return 'Einkaufsliste';

      case 'thread':
        return 'Diskussion';
    }
  }


  getTypeIcon(
    type:
      CommunityPreview['type']
  ): string {

    switch (
      type
    ) {

      case 'recipe':
        return '🍴';

      case 'list':
        return '🛒';

      case 'thread':
        return '💬';
    }
  }

}