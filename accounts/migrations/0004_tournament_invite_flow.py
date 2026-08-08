import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_discipline"),
    ]

    operations = [
        migrations.DeleteModel(name="Discipline"),
        migrations.DeleteModel(name="Tournament"),
        migrations.CreateModel(
            name="Discipline",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Tournament",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "invite_code",
                    models.CharField(db_index=True, max_length=16, unique=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("waiting", "Waiting for opponent"),
                            ("selecting", "Selecting disciplines"),
                            ("active", "Active"),
                        ],
                        default="waiting",
                        max_length=20,
                    ),
                ),
                ("result", models.IntegerField(blank=True, null=True)),
                ("start_time", models.DateTimeField(blank=True, null=True)),
                ("end_time", models.DateTimeField(blank=True, null=True)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "host",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="hosted_tournaments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "disciplines",
                    models.ManyToManyField(
                        blank=True,
                        related_name="tournaments",
                        to="accounts.discipline",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TournamentPlayer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_ready", models.BooleanField(default=False)),
                (
                    "joined_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "selected_disciplines",
                    models.ManyToManyField(
                        blank=True,
                        related_name="player_selections",
                        to="accounts.discipline",
                    ),
                ),
                (
                    "tournament",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="players",
                        to="accounts.tournament",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tournament_players",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["joined_at"],
                "unique_together": {("tournament", "user")},
            },
        ),
        migrations.AddField(
            model_name="tournament",
            name="users",
            field=models.ManyToManyField(
                blank=True,
                related_name="tournaments",
                through="accounts.TournamentPlayer",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
