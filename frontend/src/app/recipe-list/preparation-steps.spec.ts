import {
  parsePreparationSteps,
  serializePreparationSteps
} from './preparation-steps';


describe('preparation step serialization', () => {
  it('keeps multiple lines inside one step', () => {
    const instructions = serializePreparationSteps([
      '111\n222\n333'
    ]);

    expect(instructions).toBe(
      '1. 111\n   222\n   333'
    );

    expect(
      parsePreparationSteps(instructions)
    ).toEqual([
      '111\n222\n333'
    ]);
  });


  it('recognizes only numbered main lines as new steps', () => {
    expect(
      parsePreparationSteps(
        '1. Schneiden\nLangsam arbeiten\n2. Kochen'
      )
    ).toEqual([
      'Schneiden\nLangsam arbeiten',
      'Kochen'
    ]);
  });


  it('preserves a numbered-looking continuation line', () => {
    const steps = [
      'Teig vorbereiten\n2. Variante ohne Zucker'
    ];

    expect(
      parsePreparationSteps(
        serializePreparationSteps(steps)
      )
    ).toEqual(steps);
  });
});
