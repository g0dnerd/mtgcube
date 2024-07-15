from django.db import models
from django.utils import timezone
from mtgcube.users.models import User


class Tournament(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    start_datetime = models.DateTimeField(default=timezone.now)
    end_datetime = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    @classmethod
    def get_default_pk(cls):
        tournament, _ = cls.objects.get_or_create(name="Cube Open Hamburg 2024")
        return tournament.pk


class Phase(models.Model):
    id = models.AutoField(primary_key=True)
    tournament = models.ForeignKey("Tournament", on_delete=models.CASCADE)
    phase_idx = models.IntegerField("Phase Number", default=1)
    round_number = models.IntegerField("Amount of rounds", default=3)
    current_round = models.IntegerField(default=1)

    class Meta:
        unique_together = ["tournament", "phase_idx"]

    def __str__(self):
        return f"{self.tournament.name} - Phase {self.id}"


class Draft(models.Model):
    id = models.AutoField(primary_key=True)
    phase = models.ForeignKey("Phase", on_delete=models.CASCADE)
    cube = models.ForeignKey("Cube", on_delete=models.CASCADE)
    enrollments = models.ManyToManyField("Enrollment")
    round_number = models.IntegerField("Amount of rounds", default=3)
    seated = models.BooleanField(default=False)

    class Meta:
        unique_together = ["phase", "cube"]

    def __str__(self):
        return f"{self.phase} - Draft {self.id} ({self.cube.name})"


class Round(models.Model):
    id = models.AutoField(primary_key=True)
    draft = models.ForeignKey("Draft", on_delete=models.CASCADE)
    round_idx = models.IntegerField("Round number", default=1)
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)

    class Meta:
        unique_together = ["draft", "round_idx"]

    def __str__(self):
        return f"{self.draft} - Round {self.round_idx}"

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.user.username


class Enrollment(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    enrolled_on = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    pmw = models.FloatField(default=0)
    omw = models.FloatField(default=0)
    pgw = models.FloatField(default=0)
    ogw = models.FloatField(default=0)
    pairings = models.ManyToManyField(
        "self", blank=True
    )  # needs to be reset after a draft finishes
    seat = models.IntegerField(default=0)
    paired = models.BooleanField(default=False)
    had_bye = models.BooleanField(default=False)
    judge_note = models.CharField(max_length=450, blank=True)

    class Meta:
        unique_together = ("player", "tournament")

    def __str__(self):
        return f"{self.player.user.username} in {self.tournament.name}"


class Game(models.Model):
    id = models.AutoField(primary_key=True)
    round = models.ForeignKey("Round", on_delete=models.CASCADE)
    table = models.IntegerField(default=0)
    player1 = models.ForeignKey(
        "Enrollment", related_name="player1", on_delete=models.CASCADE
    )
    player2 = models.ForeignKey(
        "Enrollment", related_name="player2", on_delete=models.CASCADE
    )
    player1_wins = models.IntegerField(default=0)
    player2_wins = models.IntegerField(default=0)
    result = models.CharField(max_length=200, blank=True, null=True)
    result_reported_by = models.IntegerField(default=0)
    result_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Round {self.round.round_idx}, Table {self.table}: {self.player1.player.user.name} vs {self.player2.player.user.name}"

    def game_result_formatted(self):
        if not self.result:
            return "Pending"
        else:
            if not self.result_confirmed:
                return self.result + " (awaiting confirmation)"
            return self.result + " (confirmed)"

    def game_formatted(self):
        p1 = self.player1.player.user.name
        p1name = p1 if p1 else self.player1.player.user.username
        p2 = self.player2.player.user.name
        p2name = p2 if p2 else self.player2.player.user.username
        return f"Table {self.table}: {p1name} - {p2name}"


class Cube(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=255)
    url = models.URLField("URL", max_length=200, unique=True)

    def __str__(self):
        return self.name
