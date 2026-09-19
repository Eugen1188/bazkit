# Gemeinsame UI-Bausteine

Neue Oberflächen verwenden die Bausteine in diesem Verzeichnis, damit
Hell-/Dunkelmodus, Fokuszustände, Abstände und Bedienverhalten nicht pro Seite
neu implementiert werden.

- Karten: `appUiCard`
- Dialogflächen: `appUiDialog` und ein zugängliches `role="dialog"`
- Buttons: `appUiButton="primary|secondary|danger|quiet"`
- Normale Zahlenfelder: `appUiNumberInput` (markiert den Wert beim Anklicken)
- Mengen mit sichtbaren Auf-/Ab-Tasten: `app-ui-quantity-input`
- Lade-, Leer- und Fehlerzustände: `app-ui-state`
- Symbole: `app-ui-icon`

`npm run test:ui-architecture` prüft alle tatsächlich eingebundenen Templates
und verhindert neue Sonderlösungen für Dialoge oder Zahlenfelder. Zusätzlich
begrenzt die Prüfung die Größe einzelner Komponenten-Styles, damit neue Regeln
rechtzeitig in wiederverwendbare Bausteine verschoben werden.
