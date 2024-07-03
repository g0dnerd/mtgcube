from django.db import models
from django.utils import timezone
from mtgcube.users.models import User

class Tournament(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    round_number = models.IntegerField(default=0)
    current_round = models.IntegerField(default=0)
    start_datetime = models.DateTimeField(default=timezone.now)
    end_datetime = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
    
    @classmethod
    def get_default_pk(cls):
        tournament, _ = cls.objects.get_or_create(
            name='Cube Open Hamburg 2024')
        return tournament.pk

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
    pairings = models.ManyToManyField('self', blank=True)
    paired = models.BooleanField(default=False)
    had_bye = models.BooleanField(default=False)
    judge_note = models.CharField(max_length=450, blank=True)

    class Meta:
        unique_together = ('player', 'tournament')

    def __str__(self):
        return f'{self.player.user.username} in {self.tournament.name}'
    
class Game(models.Model):
    id = models.AutoField(primary_key=True)
    round = models.IntegerField(default=0)
    table = models.IntegerField(default=0)
    tournament = models.ForeignKey('Tournament', on_delete=models.CASCADE, default=Tournament.get_default_pk)
    player1 = models.ForeignKey('Enrollment', related_name='player1', on_delete=models.CASCADE)
    player2 = models.ForeignKey('Enrollment', related_name='player2', on_delete=models.CASCADE)
    player1_wins = models.IntegerField(default=0)
    player2_wins = models.IntegerField(default=0)
