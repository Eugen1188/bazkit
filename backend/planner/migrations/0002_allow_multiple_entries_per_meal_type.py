from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("planner", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="weeklyplanentry",
            name="unique_weekly_plan_slot",
        ),
        migrations.AlterModelOptions(
            name="weeklyplanentry",
            options={"ordering": ["date", "meal_type", "created_at", "id"]},
        ),
    ]
