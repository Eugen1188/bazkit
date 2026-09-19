import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';


const root = process.cwd();
const appRoot = path.join(root, 'src', 'app');
const failures = [];

function walk(directory, extension, files = []) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) walk(target, extension, files);
    else if (target.endsWith(extension)) files.push(target);
  }
  return files;
}

const activeTemplates = new Set();
for (const componentPath of walk(appRoot, '.ts')) {
  const source = fs.readFileSync(componentPath, 'utf8');
  for (const match of source.matchAll(/templateUrl\s*:\s*['"]([^'"]+)['"]/g)) {
    activeTemplates.add(path.resolve(path.dirname(componentPath), match[1]));
  }
}

for (const templatePath of activeTemplates) {
  const source = fs.readFileSync(templatePath, 'utf8');
  const relative = path.relative(root, templatePath);
  const isQuantityComponent = relative.endsWith(
    path.join('components', 'ui-quantity-input', 'ui-quantity-input.component.html'),
  );
  for (const match of source.matchAll(/<[^>]+role=["']dialog["'][^>]*>/gis)) {
    if (!/\bappUiDialog\b/.test(match[0])) {
      failures.push(`${relative}: Dialoge müssen appUiDialog verwenden.`);
    }
  }
  for (const match of source.matchAll(/<input\b[^>]*type=["']number["'][^>]*>/gis)) {
    if (isQuantityComponent) continue;
    if (!/\bappUiNumberInput\b/.test(match[0])) {
      failures.push(`${relative}: Zahlenfelder müssen appUiNumberInput verwenden.`);
    }
  }
}

for (const stylePath of walk(appRoot, '.scss')) {
  const source = fs.readFileSync(stylePath, 'utf8');
  const nonEmptyLines = source.split(/\r?\n/).filter(line => line.trim()).length;
  if (nonEmptyLines > 2300) {
    failures.push(
      `${path.relative(root, stylePath)}: ${nonEmptyLines} aktive Style-Zeilen; Maximum ist 2300.`,
    );
  }
}

const primitives = fs.readFileSync(
  path.join(appRoot, 'components', 'ui-primitives', 'ui-primitives.directive.ts'),
  'utf8',
);
for (const primitive of [
  'UiCardDirective',
  'UiDialogDirective',
  'UiButtonDirective',
  'UiNumberInputDirective',
]) {
  if (!primitives.includes(`class ${primitive}`)) {
    failures.push(`Gemeinsamer UI-Baustein ${primitive} fehlt.`);
  }
}

for (const component of ['ui-quantity-input', 'ui-state', 'ui-icon']) {
  const componentDirectory = path.join(appRoot, 'components', component);
  if (!fs.existsSync(componentDirectory)) {
    failures.push(`Gemeinsame Komponente ${component} fehlt.`);
  }
}

if (failures.length) {
  console.error('UI-Architekturprüfung fehlgeschlagen:\n');
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(
  `UI-Architektur geprüft: ${activeTemplates.size} aktive Templates, gemeinsame Dialoge und Zahlenfelder.`,
);
