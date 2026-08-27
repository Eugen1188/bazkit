import {
  Component
} from '@angular/core';

import {
  CommonModule
} from '@angular/common';

import {
  RouterLink
} from '@angular/router';
import { UiIconComponent } from '../components/ui-icon/ui-icon.component';


@Component({
  selector:
    'app-home',

  standalone:
    true,

  imports: [
    CommonModule,
    RouterLink,
    UiIconComponent
  ],

  templateUrl:
    './home.component.html',

  styleUrl:
    './home.component.scss'
})
export class HomeComponent {

}
