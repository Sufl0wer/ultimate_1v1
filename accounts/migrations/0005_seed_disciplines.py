from django.db import migrations


DISCIPLINES = [
    ("Aim Duel", "Head-to-head aim challenge."),
    ("Speed Run", "Complete the course as fast as possible."),
    ("Puzzle Rush", "Solve puzzles under time pressure."),
    ("Reaction Test", "React faster than your opponent."),
    ("Trivia Battle", "Answer questions across mixed topics."),
]


def seed_disciplines(apps, schema_editor):
    Discipline = apps.get_model("accounts", "Discipline")
    for name, description in DISCIPLINES:
        Discipline.objects.get_or_create(
            name=name,
            defaults={"description": description},
        )


def unseed_disciplines(apps, schema_editor):
    Discipline = apps.get_model("accounts", "Discipline")
    Discipline.objects.filter(name__in=[name for name, _ in DISCIPLINES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_tournament_invite_flow"),
    ]

    operations = [
        migrations.RunPython(seed_disciplines, unseed_disciplines),
    ]
