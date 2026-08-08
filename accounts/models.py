import secrets
import string

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        ordering = ["email"]

    def __str__(self) -> str:
        return self.email


class Discipline(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


def generate_invite_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Tournament(models.Model):
    STATUS_WAITING = "waiting"
    STATUS_SELECTING = "selecting"
    STATUS_ACTIVE = "active"
    STATUS_CHOICES = [
        (STATUS_WAITING, "Waiting for opponent"),
        (STATUS_SELECTING, "Selecting disciplines"),
        (STATUS_ACTIVE, "Active"),
    ]

    invite_code = models.CharField(max_length=16, unique=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_WAITING,
    )
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hosted_tournaments",
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="TournamentPlayer",
        related_name="tournaments",
        blank=True,
    )
    disciplines = models.ManyToManyField(
        Discipline,
        related_name="tournaments",
        blank=True,
    )
    result = models.IntegerField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Tournament #{self.pk} ({self.invite_code})"

    @classmethod
    def create_with_host(cls, host: User) -> "Tournament":
        for _ in range(20):
            code = generate_invite_code()
            if not cls.objects.filter(invite_code=code).exists():
                tournament = cls.objects.create(
                    invite_code=code,
                    status=cls.STATUS_WAITING,
                    host=host,
                )
                TournamentPlayer.objects.create(tournament=tournament, user=host)
                return tournament
        raise RuntimeError("Could not generate a unique invite code")

    def player_count(self) -> int:
        return self.players.count()

    def both_players_ready(self) -> bool:
        players = list(self.players.all())
        return len(players) == 2 and all(player.is_ready for player in players)

    def activate_if_ready(self) -> bool:
        if self.status == self.STATUS_ACTIVE:
            return True
        if not self.both_players_ready():
            return False

        selected_ids = set()
        for player in self.players.prefetch_related("selected_disciplines"):
            selected_ids.update(
                player.selected_disciplines.values_list("id", flat=True)
            )

        self.status = self.STATUS_ACTIVE
        self.start_time = timezone.now()
        self.save(update_fields=["status", "start_time"])
        self.disciplines.set(selected_ids)
        return True


class TournamentPlayer(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="players",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tournament_players",
    )
    is_ready = models.BooleanField(default=False)
    selected_disciplines = models.ManyToManyField(
        Discipline,
        related_name="player_selections",
        blank=True,
    )
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("tournament", "user")]
        ordering = ["joined_at"]

    def __str__(self) -> str:
        return f"{self.user} in {self.tournament}"
