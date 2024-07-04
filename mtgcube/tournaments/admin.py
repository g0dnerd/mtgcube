from django.contrib import admin

from .models import Tournament, Game, Enrollment, Player

# Register your models here.
class GameInline(admin.TabularInline):
    model = Game
    extra = 3

class GameAdmin(admin.ModelAdmin):
    fields = ['table', 'player1', 'player2', 'player1_wins', 'player2_wins', 'result', 'result_reported_by', 'result_confirmed']

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    fields = ['player', 'score', 'games_played', 'games_won', 'judge_note']
    extra = 3

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'player', 'score', 'games_played', 'games_won', 'judge_note']
    fields = ['tournament', 'player', 'score', 'games_played', 'games_won', 'pairings', 'paired', 'judge_note']

class PlayerInline(admin.TabularInline):
    model = Player
    fields = ['user', 'name']
    extra = 3

class PlayerAdmin(admin.ModelAdmin):
    list_display = ['user', 'name']
    fields = ['user', 'name']

class TournamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'current_round']
    fields = ['name', 'round_number', 'current_round', 'round_length', 'round_timer_start']
    inlines = [EnrollmentInline, GameInline]

admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Game, GameAdmin)