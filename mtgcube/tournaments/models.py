from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
from mtgcube.users.models import User
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


class Tournament(models.Model):
    id = models.AutoField(primary_key=True)
    public = models.BooleanField(default=False)
    name = models.CharField(max_length=50, unique=True)
    start_datetime = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True)
    format_description = models.TextField(blank=True)
    player_capacity = models.IntegerField(default=0)
    signed_up = models.IntegerField(default=0)
    end_datetime = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=255, blank=True)
    announcement = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(unique=True)
    current_round = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    @classmethod
    def get_default_pk(cls):
        tournament, __ = cls.objects.get_or_create(name="Cube Open Hamburg 2024")
        return tournament.pk


class SideEvent(Tournament):
    tournament = models.ForeignKey(
        Tournament, related_name="side_events", on_delete=models.CASCADE
    )


class Phase(models.Model):
    id = models.AutoField(primary_key=True)
    tournament = models.ForeignKey("Tournament", on_delete=models.CASCADE)
    phase_idx = models.IntegerField("Phase Number", default=1)
    round_number = models.IntegerField("Amount of rounds", default=3)
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.phase_idx == 1:
            self.started = True
        super(Phase, self).save(*args, **kwargs)

    class Meta:
        unique_together = ["tournament", "phase_idx"]

    def __str__(self):
        return f"{self.tournament.name} - Phase {self.phase_idx}"


class Draft(models.Model):
    id = models.AutoField(primary_key=True)
    phase = models.ForeignKey("Phase", on_delete=models.CASCADE)
    cube = models.ForeignKey("Cube", on_delete=models.CASCADE)
    enrollments = models.ManyToManyField("Enrollment")
    round_number = models.IntegerField("Amount of rounds", default=3)
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    seated = models.BooleanField(default=False)
    slug = models.SlugField(unique=True)

    class Meta:
        unique_together = ["phase", "cube"]

    def __str__(self):
        return f"{self.phase} - Draft {self.id} ({self.cube.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(
                f"{self.phase.tournament.name}{self.phase.phase_idx}{self.cube.name}"
            )
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("tournaments:admin_draft_dashboard", kwargs={"slug": self.slug})


class Round(models.Model):
    id = models.AutoField(primary_key=True)
    draft = models.ForeignKey("Draft", on_delete=models.CASCADE)
    round_idx = models.IntegerField("Round number", default=1)
    paired = models.BooleanField(default=False)
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)

    class Meta:
        unique_together = ["draft", "round_idx"]

    def __str__(self):
        return f"{self.draft} - Round {self.round_idx}"


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default="")

    def __str__(self):
        return self.user.name


class Enrollment(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    dropped = models.BooleanField(default=False)
    enrolled_on = models.DateTimeField(auto_now_add=True)
    registration_finished = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    pmw = models.FloatField(default=0)
    omw = models.FloatField(default=0)
    pgw = models.FloatField(default=0)
    ogw = models.FloatField(default=0)
    draft_score = models.IntegerField(default=0)
    draft_games_played = models.IntegerField(default=0)
    draft_games_won = models.IntegerField(default=0)
    draft_pmw = models.FloatField(default=0)
    draft_omw = models.FloatField(default=0)
    draft_pgw = models.FloatField(default=0)
    draft_ogw = models.FloatField(default=0)
    draft_place = models.PositiveIntegerField(default=0)
    tournament_place = models.PositiveIntegerField(default=0)
    checked_in = models.BooleanField(default=False)
    checked_out = models.BooleanField(default=False)
    pairings = models.ManyToManyField("self", blank=True)
    seat = models.IntegerField(default=0)
    paired = models.BooleanField(default=False)
    had_bye = models.BooleanField(default=False)
    bye_this_round = models.BooleanField(default=False)
    judge_note = models.CharField(max_length=450, blank=True)

    class Meta:
        unique_together = ("player", "tournament")

    def __str__(self):
        return f"{self.player.user.name} in {self.tournament.name}"


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
    result_reported_by = models.CharField(max_length=255, blank=True, null=True)
    result_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Round {self.round.round_idx}, Table {self.table}: {self.player1.player.user.name} vs {self.player2.player.user.name}"

    def game_result_formatted(self):
        if not self.result:
            return "Pending"
        else:
            if not self.result_confirmed:
                trans = _("(awaiting confirmation)")
                return self.result + f" {trans}"
            trans = _("(confirmed)")
            return self.result + f" {trans}"

    def game_formatted(self):
        p1 = self.player1.player.user.name
        p1name = p1 if p1 else self.player1.player.user.name
        p2 = self.player2.player.user.name
        p2name = p2 if p2 else self.player2.player.user.name
        return f"Table {self.table}: {p1name} - {p2name}"


def cube_directory_path(instance, filename):
    return f"images/cube_thumbnails/{instance.name}_{filename}"


class Cube(models.Model):
    id = models.AutoField(primary_key=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200, unique=True)
    card_number = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    special_rules = models.TextField(blank=True)
    url = models.URLField("URL", max_length=200, unique=True)
    image = models.ImageField(upload_to=cube_directory_path, blank=True)
    slug = models.SlugField(null=True)

    def __str__(self):
        return self.name


def user_directory_path(instance, filename):
    return f"images/userupload/{instance.user.id}/{filename}"


class Image(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=user_directory_path)
    draft_idx = models.IntegerField("Draft ID", default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    checkin = models.BooleanField(default=True)

    def __str__(self):
        img_time_fstring = self.uploaded_at.time().strftime("%H:%M:%S")
        return f"{self.user} - Draft {self.draft_idx} ({img_time_fstring})"
