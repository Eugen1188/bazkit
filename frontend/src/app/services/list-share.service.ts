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
  ): Promise<'shared' | 'copied' | 'cancelled'> {

    const text =
      this.createShareText(
        title,
        items
      );


    if (
      navigator.share
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

        if (
          error instanceof DOMException &&
          error.name === 'AbortError'
        ) {

          return 'cancelled';
        }


        console.error(
          'Native Teilen-Funktion fehlgeschlagen:',
          error
        );
      }

    }


    await navigator.clipboard.writeText(
      text
    );

    return 'copied';
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
            item.unit?.trim()
            ?? '';


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


          const noteText =
            item.note?.trim()
              ? ` (${item.note.trim()})`
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

    if (
      Number.isInteger(
        Number(quantity)
      )
    ) {

      return String(
        Number(quantity)
      );
    }


    return Number(
      quantity
    )
      .toFixed(2)
      .replace(
        '.',
        ','
      )
      .replace(
        /,?0+$/,
        ''
      );
  }
}