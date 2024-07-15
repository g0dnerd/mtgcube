from django.contrib import admin

from .models import Tournament, Game, Enrollment, Player, Phase, Round, Draft, Cube


# Register your models here.
class GameInline(admin.TabularInline):
    model = Game
    extra = 3


class GameAdmin(admin.ModelAdmin):
    readonly_fields = ("id", )
    fields = [
        "id",
        "round",
        "player1",
        "player2",
        "table",
        "player1_wins",
        "player2_wins",
        "result",
        "result_reported_by",
        "result_confirmed",
    ]


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    fields = ["player", "score", "games_played", "games_won", "judge_note"]
    extra = 3


class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        "tournament",
        "player",
        "score",
        "games_played",
        "games_won",
        "judge_note",
    ]
    fields = [
        "tournament",
        "player",
        "score",
        "games_played",
        "games_won",
        "pairings",
        "paired",
        "judge_note",
    ]


class PlayerInline(admin.TabularInline):
    model = Player
    fields = ["user", "name"]
    extra = 3


class PlayerAdmin(admin.ModelAdmin):
    list_display = ["user", "name"]
    fields = ["user", "name"]


class TournamentAdmin(admin.ModelAdmin):
    list_display = ["name"]
    fields = ["name", "start_datetime", "end_datetime"]


class PhaseAdmin(admin.ModelAdmin):
    fields = [
        "tournament",
        "phase_idx",
        "round_number",
        "current_round",
    ]


class DraftAdmin(admin.ModelAdmin):
    fields = ["phase", "cube", "enrollments", "round_number"]


class RoundAdmin(admin.ModelAdmin):
    fields = ["draft", "round_idx", "round_length"]


class CubeAdmin(admin.ModelAdmin):
    fields = ["name", "description", "url"]


admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Phase, PhaseAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Draft, DraftAdmin)
admin.site.register(Round, RoundAdmin)
admin.site.register(Cube, CubeAdmin)
