from django.contrib import admin

from .models import Tournament, Game, Enrollment, Player, Phase, Round, Draft, Cube, Image, SideEvent


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
        "draft_score",
        "draft_games_played",
        "draft_games_won",
    ]
    fields = [
        "tournament",
        "player",
        "registration_finished",
        "dropped",
        "checked_in",
        "checked_out",
        "score",
        "games_played",
        "games_won",
        "omw",
        "pgw",
        "ogw",
        "draft_score",
        "draft_games_played",
        "draft_games_won",
        "draft_omw",
        "draft_pgw",
        "draft_ogw",
        "pairings",
        "paired",
        "bye_this_round",
        "judge_note",
    ]


class PlayerInline(admin.TabularInline):
    model = Player
    fields = ["user"]
    extra = 3


class PlayerAdmin(admin.ModelAdmin):
    list_display = ["user"]
    fields = ["user"]


class TournamentAdmin(admin.ModelAdmin):
    list_display = ["name"]
    fields = ["name", "public", "description", "format_description", "player_capacity", "signed_up", "current_round", "location", "announcement", "start_datetime", "end_datetime", "slug"]
    prepopulated_fields = {"slug": ("name", )}


class SideEventAdmin(admin.ModelAdmin):
    list_display = ["name"]
    fields = ["tournament", "name", "description", "format_description", "player_capacity", "signed_up", "location", "announcement", "start_datetime", "end_datetime"]


class PhaseAdmin(admin.ModelAdmin):
    fields = [
        "tournament",
        "phase_idx",
        "started",
        "finished",
        "round_number",
    ]

class DraftAdmin(admin.ModelAdmin):
    fields = ["phase", "cube", "enrollments", "round_number", "seated", "started", "finished", "slug"]


class RoundAdmin(admin.ModelAdmin):
    fields = ["draft", "round_idx", "paired", "started", "finished"]


class CubeAdmin(admin.ModelAdmin):
    fields = ["name", "slug", "creator", "card_number", "description", "special_rules", "url", "image"]

class ImageAdmin(admin.ModelAdmin):
    fields = ["user", "draft_idx", "image"]


admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Phase, PhaseAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Draft, DraftAdmin)
admin.site.register(Round, RoundAdmin)
admin.site.register(Cube, CubeAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(SideEvent, SideEventAdmin)
