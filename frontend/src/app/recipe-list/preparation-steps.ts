const STEP_PREFIX = /^(\d+)[.)]\s+(.*)$/;


function normalizeLineBreaks(
  value: string
): string {
  return value.replace(/\r\n?/g, '\n');
}


export function serializePreparationSteps(
  steps: string[]
): string {
  return steps
    .map(step =>
      normalizeLineBreaks(step).trim()
    )
    .filter(Boolean)
    .map((step, index) => {
      const [firstLine, ...continuationLines] =
        step.split('\n');

      return [
        `${index + 1}. ${firstLine}`,
        ...continuationLines.map(
          line => `   ${line}`
        )
      ].join('\n');
    })
    .join('\n');
}


export function parsePreparationSteps(
  instructions: string
): string[] {
  const normalized =
    normalizeLineBreaks(instructions).trim();

  if (!normalized) {
    return [];
  }

  const steps: string[] = [];
  let currentLines: string[] = [];

  const finishCurrentStep = (): void => {
    const step = currentLines
      .join('\n')
      .trim();

    if (step) {
      steps.push(step);
    }

    currentLines = [];
  };

  for (const line of normalized.split('\n')) {
    const numberedStep = line.match(STEP_PREFIX);

    if (numberedStep) {
      finishCurrentStep();
      currentLines = [numberedStep[2]];
      continue;
    }

    const continuationLine = line.startsWith('   ')
      ? line.slice(3)
      : line;

    currentLines.push(continuationLine);
  }

  finishCurrentStep();

  return steps;
}
