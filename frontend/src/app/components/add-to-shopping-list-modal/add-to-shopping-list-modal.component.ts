import {
  Component,
  EventEmitter,
  OnDestroy,
  OnInit,
  Output
} from '@angular/core';


@Component({
  selector:
    'app-add-to-shopping-list-modal',

  standalone: true,

  imports: [],

  templateUrl:
    './add-to-shopping-list-modal.component.html',

  styleUrl:
    './add-to-shopping-list-modal.component.scss'
})
export class AddToShoppingListModalComponent
implements OnInit, OnDestroy {

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