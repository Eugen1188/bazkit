import { Directive, HostBinding, Input } from '@angular/core';


@Directive({
  selector: '[appUiCard]',
  standalone: true,
})
export class UiCardDirective {
  @HostBinding('class.ui-card') readonly uiCardClass = true;
}


@Directive({
  selector: '[appUiDialog]',
  standalone: true,
})
export class UiDialogDirective {
  @HostBinding('class.ui-dialog') readonly uiDialogClass = true;
}


@Directive({
  selector: '[appUiButton]',
  standalone: true,
})
export class UiButtonDirective {
  @Input() appUiButton: 'primary' | 'secondary' | 'danger' | 'quiet' = 'secondary';
  @HostBinding('class.ui-button') readonly uiButtonClass = true;

  @HostBinding('class.ui-button--primary')
  get isPrimary(): boolean { return this.appUiButton === 'primary'; }

  @HostBinding('class.ui-button--secondary')
  get isSecondary(): boolean { return this.appUiButton === 'secondary'; }

  @HostBinding('class.ui-button--danger')
  get isDanger(): boolean { return this.appUiButton === 'danger'; }

  @HostBinding('class.ui-button--quiet')
  get isQuiet(): boolean { return this.appUiButton === 'quiet'; }
}
