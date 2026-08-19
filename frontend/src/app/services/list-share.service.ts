import {
  Injectable
} from '@angular/core';


export interface ShareListItem {
  name: string;

  quantity?: number | null;

  unit?: string;

  note?: string;

  isChecked?: boolean;
}


@Injectable({
  providedIn: 'root'
})
export class ListShareService {

  async shareList(
    title: string,
    items: ShareListItem[]
  ): Promise<
    'shared' |
    'copied' |
    'cancelled'
  > {

    const text =
      this.createShareText(
        title,
        items
      );


    /*
     * Native Share API
     *
     * Funktioniert z. B. auf Smartphones
     * und später sauber über HTTPS.
     */
    if (
      typeof navigator !== 'undefined' &&
      typeof navigator.share === 'function'
    ) {

      try {

        await navigator.share({
          title,
          text
        });


        return 'shared';

      } catch (
        error: unknown
      ) {

        /*
         * Nutzer hat das Teilen-Menü
         * einfach geschlossen.
         */
        if (
          error instanceof DOMException &&
          error.name === 'AbortError'
        ) {

          return 'cancelled';
        }


        console.warn(
          'Native Share API nicht verfügbar:',
          error
        );
      }

    }


    /*
     * Moderne Clipboard API
     */
    if (
      typeof navigator !== 'undefined' &&
      navigator.clipboard &&
      typeof navigator.clipboard.writeText ===
        'function'
    ) {

      try {

        await navigator.clipboard.writeText(
          text
        );


        return 'copied';

      } catch (
        error
      ) {

        console.warn(
          'Clipboard API konnte nicht verwendet werden:',
          error
        );
      }

    }


    /*
     * Fallback für HTTP / ältere Browser.
     *
     * Damit funktioniert es auch aktuell
     * über deine Server-IP.
     */
    const copied =
      this.copyWithFallback(
        text
      );


    if (
      copied
    ) {

      return 'copied';
    }


    throw new Error(
      'Liste konnte weder geteilt noch kopiert werden.'
    );
  }


  private createShareText(
    title: string,
    items: ShareListItem[]
  ): string {

    const lines =
      items.map(
        item => {

          const check =
            item.isChecked
              ? '☑'
              : '☐';


          const quantity =
            item.quantity !== null &&
            item.quantity !== undefined
              ? this.formatQuantity(
                  item.quantity
                )
              : '';


          const unit =
            item.unit?.trim() ?? '';


          const amount =
            [
              quantity,
              unit
            ]
              .filter(
                value =>
                  value.length > 0
              )
              .join(' ');


          const amountText =
            amount
              ? ` – ${amount}`
              : '';


          const note =
            item.note?.trim()
            ?? '';


          const noteText =
            note
              ? ` (${note})`
              : '';


          return (
            `${check} ${item.name}${amountText}${noteText}`
          );
        }
      );


    return [
      `🛒 ${title}`,
      '',
      ...lines,
      '',
      'Erstellt mit Bazkit'
    ].join('\n');
  }


  private formatQuantity(
    quantity: number
  ): string {

    const numericQuantity =
      Number(
        quantity
      );


    if (
      Number.isInteger(
        numericQuantity
      )
    ) {

      return String(
        numericQuantity
      );
    }


    return numericQuantity
      .toFixed(2)
      .replace(
        '.',
        ','
      )
      .replace(
        /0+$/,
        ''
      )
      .replace(
        /,$/,
        ''
      );
  }


  private copyWithFallback(
    text: string
  ): boolean {

    if (
      typeof document === 'undefined'
    ) {

      return false;
    }


    const textarea =
      document.createElement(
        'textarea'
      );


    textarea.value =
      text;


    textarea.setAttribute(
      'readonly',
      ''
    );


    textarea.style.position =
      'fixed';

    textarea.style.left =
      '-9999px';

    textarea.style.top =
      '-9999px';

    textarea.style.opacity =
      '0';


    document.body.appendChild(
      textarea
    );


    textarea.focus();

    textarea.select();


    let successful =
      false;


    try {

      successful =
        document.execCommand(
          'copy'
        );

    } catch (
      error
    ) {

      console.error(
        'Fallback-Kopieren fehlgeschlagen:',
        error
      );

      successful =
        false;
    }


    document.body.removeChild(
      textarea
    );


    return successful;
  }
}