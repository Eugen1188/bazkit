import {
  Component
} from '@angular/core';

import {
  RouterOutlet
} from '@angular/router';

import {
  SidebarComponent
} from '../sidebar/sidebar.component';


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
export class MainComponent {

}