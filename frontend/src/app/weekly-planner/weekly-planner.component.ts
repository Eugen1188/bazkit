import {
  CommonModule
} from '@angular/common';

import {
  Component
} from '@angular/core';


type MealType =
  'breakfast' |
  'lunch' |
  'dinner';


interface Meal {
  id: number;

  name: string;

  image?: string;

  calories: number;

  protein: number;

  carbohydrates: number;

  fat: number;

  servings: number;
}


interface PlannerDay {
  fullName: string;

  shortName: string;

  date: string;

  dayNumber: number;

  isToday?: boolean;

  breakfast:
    Meal | null;

  lunch:
    Meal | null;

  dinner:
    Meal | null;
}


@Component({
  selector:
    'app-weekly-planner',

  standalone:
    true,

  imports: [
    CommonModule
  ],

  templateUrl:
    './weekly-planner.component.html',

  styleUrl:
    './weekly-planner.component.scss'
})
export class WeeklyPlannerComponent {

  weekLabel =
    '24. – 30. August';


  selectedDayIndex =
    0;


  mealTypes: {
    key: MealType;
    label: string;
  }[] = [

    {
      key:
        'breakfast',

      label:
        'Frühstück'
    },

    {
      key:
        'lunch',

      label:
        'Mittagessen'
    },

    {
      key:
        'dinner',

      label:
        'Abendessen'
    }

  ];


  days:
    PlannerDay[] = [

    {
      fullName:
        'Montag',

      shortName:
        'Mo',

      date:
        '24. August',

      dayNumber:
        24,

      isToday:
        true,

      breakfast: {
        id:
          1,

        name:
          'Overnight Oats',

        image:
          'assets/images/home/home-ai-food.webp',

        calories:
          420,

        protein:
          22,

        carbohydrates:
          54,

        fat:
          13,

        servings:
          1
      },

      lunch: {
        id:
          2,

        name:
          'Chicken Caesar Salad',

        image:
          'assets/images/home/home-food.webp',

        calories:
          590,

        protein:
          41,

        carbohydrates:
          34,

        fat:
          29,

        servings:
          1
      },

      dinner: {
        id:
          3,

        name:
          'Pasta Bolognese',

        image:
          'assets/images/home/home-recipes.webp',

        calories:
          710,

        protein:
          38,

        carbohydrates:
          82,

        fat:
          24,

        servings:
          2
      }
    },


    {
      fullName:
        'Dienstag',

      shortName:
        'Di',

      date:
        '25. August',

      dayNumber:
        25,

      breakfast: {
        id:
          4,

        name:
          'Joghurt mit Früchten',

        image:
          'assets/images/home/home-ai-food.webp',

        calories:
          360,

        protein:
          24,

        carbohydrates:
          45,

        fat:
          8,

        servings:
          1
      },

      lunch:
        null,

      dinner: {
        id:
          5,

        name:
          'Hähnchen Curry',

        image:
          'assets/images/home/home-food.webp',

        calories:
          680,

        protein:
          46,

        carbohydrates:
          72,

        fat:
          22,

        servings:
          2
      }
    },


    {
      fullName:
        'Mittwoch',

      shortName:
        'Mi',

      date:
        '26. August',

      dayNumber:
        26,

      breakfast:
        null,

      lunch: {
        id:
          6,

        name:
          'Mediterrane Bowl',

        image:
          'assets/images/home/home-food.webp',

        calories:
          570,

        protein:
          27,

        carbohydrates:
          69,

        fat:
          21,

        servings:
          1
      },

      dinner: {
        id:
          7,

        name:
          'Lachs mit Gemüse',

        image:
          'assets/images/home/home-recipes.webp',

        calories:
          640,

        protein:
          45,

        carbohydrates:
          39,

        fat:
          31,

        servings:
          2
      }
    },


    {
      fullName:
        'Donnerstag',

      shortName:
        'Do',

      date:
        '27. August',

      dayNumber:
        27,

      breakfast:
        null,

      lunch:
        null,

      dinner: {
        id:
          8,

        name:
          'Gemüse Pasta',

        image:
          'assets/images/home/home-ai-food.webp',

        calories:
          620,

        protein:
          24,

        carbohydrates:
          88,

        fat:
          18,

        servings:
          2
      }
    },


    {
      fullName:
        'Freitag',

      shortName:
        'Fr',

      date:
        '28. August',

      dayNumber:
        28,

      breakfast:
        null,

      lunch:
        null,

      dinner: {
        id:
          9,

        name:
          'Chicken Tacos',

        image:
          'assets/images/home/home-food.webp',

        calories:
          730,

        protein:
          43,

        carbohydrates:
          76,

        fat:
          29,

        servings:
          2
      }
    },


    {
      fullName:
        'Samstag',

      shortName:
        'Sa',

      date:
        '29. August',

      dayNumber:
        29,

      breakfast:
        null,

      lunch:
        null,

      dinner:
        null
    },


    {
      fullName:
        'Sonntag',

      shortName:
        'So',

      date:
        '30. August',

      dayNumber:
        30,

      breakfast:
        null,

      lunch:
        null,

      dinner: {
        id:
          10,

        name:
          'Rinderrouladen',

        image:
          'assets/images/home/home-recipes.webp',

        calories:
          810,

        protein:
          52,

        carbohydrates:
          58,

        fat:
          38,

        servings:
          2
      }
    }

  ];


  get selectedDay():
    PlannerDay {

    return (
      this.days[
        this.selectedDayIndex
      ]
      ??
      this.days[0]
    );
  }


  get totalMeals():
    number {

    return this.days
      .reduce(
        (
          total,
          day
        ) => {

          return (
            total +
            this.getMealCount(
              day
            )
          );

        },
        0
      );
  }


  get plannedDays():
    number {

    return this.days
      .filter(
        day =>
          this.getMealCount(
            day
          ) > 0
      )
      .length;
  }


  get averageCalories():
    number {

    if (
      this.plannedDays === 0
    ) {

      return 0;
    }


    const total =
      this.days
        .reduce(
          (
            sum,
            day
          ) =>
            sum +
            this.getDayCalories(
              day
            ),
          0
        );


    return Math.round(
      total /
      this.plannedDays
    );
  }


  get averageProtein():
    number {

    if (
      this.plannedDays === 0
    ) {

      return 0;
    }


    const total =
      this.days
        .reduce(
          (
            sum,
            day
          ) =>
            sum +
            this.getDayProtein(
              day
            ),
          0
        );


    return Math.round(
      total /
      this.plannedDays
    );
  }


  getMeal(
    day:
      PlannerDay,

    type:
      MealType
  ): Meal | null {

    return day[type];
  }


  getMealCount(
    day:
      PlannerDay
  ): number {

    return [
      day.breakfast,
      day.lunch,
      day.dinner
    ]
      .filter(
        meal =>
          !!meal
      )
      .length;
  }


  getDayCalories(
    day:
      PlannerDay
  ): number {

    return [
      day.breakfast,
      day.lunch,
      day.dinner
    ]
      .reduce(
        (
          total:
            number,

          meal:
            Meal | null
        ) =>
          total +
          (
            meal?.calories ??
            0
          ),
        0
      );
  }


  getDayProtein(
    day:
      PlannerDay
  ): number {

    return [
      day.breakfast,
      day.lunch,
      day.dinner
    ]
      .reduce(
        (
          total:
            number,

          meal:
            Meal | null
        ) =>
          total +
          (
            meal?.protein ??
            0
          ),
        0
      );
  }


  addMeal(
    dayIndex:
      number,

    type:
      MealType
  ): void {

    console.log(
      'Mahlzeit hinzufügen:',
      dayIndex,
      type
    );

    /*
     * Später öffnen wir hier
     * einen Dialog mit:
     *
     * - Meine Rezepte
     * - Community
     * - eigenes Gericht
     */
  }


  openMeal(
    dayIndex:
      number,

    type:
      MealType
  ): void {

    const meal =
      this.days[
        dayIndex
      ][type];


    console.log(
      'Mahlzeit öffnen:',
      meal
    );
  }


  previousWeek():
    void {

    console.log(
      'Vorherige Woche'
    );
  }


  nextWeek():
    void {

    console.log(
      'Nächste Woche'
    );
  }


  goToCurrentWeek():
    void {

    console.log(
      'Aktuelle Woche'
    );
  }


  generateWeek():
    void {

    console.log(
      'Wochenplan mit KI erstellen'
    );
  }


  createShoppingList():
    void {

    console.log(
      'Wochenzutaten zur Einkaufsliste hinzufügen'
    );
  }

}