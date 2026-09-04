import {
  Component,
  EventEmitter,
  HostListener,
  OnDestroy,
  OnInit,
  Output
} from '@angular/core';
import { UiIconComponent } from '../ui-icon/ui-icon.component';


@Component({
  selector:
    'app-add-to-shopping-list-modal',

  standalone: true,

  imports: [UiIconComponent],

  templateUrl:
    './add-to-shopping-list-modal.component.html',

  styleUrl:
    './add-to-shopping-list-modal.component.scss'
})
export class AddToShoppingListModalComponent
implements OnInit, OnDestroy {

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.close.emit();
  }

  @Output()
  close =
    new EventEmitter<void>();


  @Output()
  addProduct =
    new EventEmitter<void>();


  @Output()
  addSavedList =
    new EventEmitter<void>();


  @Output()
  addRecipe =
    new EventEmitter<void>();


  private previousBodyOverflow = '';


  ngOnInit(): void {

    this.previousBodyOverflow =
      document.body.style.overflow;

    document.body.style.overflow =
      'hidden';
  }


  ngOnDestroy(): void {

    document.body.style.overflow =
      this.previousBodyOverflow;
  }
}
