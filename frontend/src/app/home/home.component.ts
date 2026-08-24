import {
  CommonModule
} from '@angular/common';

import {
  Component
} from '@angular/core';

import {
  RouterLink
} from '@angular/router';


@Component({
  selector: 'app-home',

  standalone: true,

  imports: [
    CommonModule,
    RouterLink
  ],

  templateUrl:
    './home.component.html',

  styleUrl:
    './home.component.scss'
})
export class HomeComponent {

  features = [
    {
      title:
        'Einkauf planen',

      text:
        'Erstelle deine Einkaufsliste schnell und ergänze Produkte mit wenigen Klicks.',

      route:
        '/main/shopping-list',

      icon:
        'shopping'
    },

    {
      title:
        'Rezepte entdecken',

      text:
        'Speichere eigene Rezepte oder lasse dir neue Ideen mit KI erstellen.',

      route:
        '/main/recipe-list',

      icon:
        'recipe'
    },

    {
      title:
        'Listen vorbereiten',

      text:
        'Speichere typische Einkäufe und füge sie später direkt wieder hinzu.',

      route:
        '/main/saved-list',

      icon:
        'list'
    }
  ];


  steps = [
    {
      number:
        '01',

      title:
        'Rezept oder Produkte wählen',

      text:
        'Starte direkt mit einem Rezept, einer gespeicherten Liste oder einzelnen Produkten.'
    },

    {
      number:
        '02',

      title:
        'Alles landet an einem Ort',

      text:
        'Bazkit bringt deine Auswahl automatisch in deiner Einkaufsliste zusammen.'
    },

    {
      number:
        '03',

      title:
        'Einfach einkaufen',

      text:
        'Hake erledigte Produkte ab und behalte jederzeit den Überblick.'
    }
  ];
}