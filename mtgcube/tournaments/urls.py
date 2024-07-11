from django.urls import path

# 1from django.views.generic import RedirectView
from . import views

app_name = "tournaments"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:tournament_id>/", views.tournament_view, name="tournament_view"),
    path(
        "<int:tournament_id>/admin/",
        views.tournament_admin_view,
        name="tournament_admin_view",
    ),
    path(
        "<int:tournament_id>/admin/<int:draft_id>/~pair",
        views.pair_round_view,
        name="pair_round_view",
    ),
    path(
        "<int:tournament_id>/admin/<int:draft_id>/~reset",
        views.clear_history_view,
        name="clear_history_view",
    ),
    path(
        "<int:tournament_id>/admin/<int:round_id>/~starttimer",
        views.start_round_view,
        name="start_round_view",
    ),
    path(
        "<int:tournament_id>/admin/<int:round_id>/~stoptimer",
        views.stop_round_view,
        name="stop_round_view",
    ),
    path(
        "<int:tournament_id>/admin/<int:draft_id>/games-for-draft/",
        views.games_for_draft,
        name="games_for_draft",
    ),
    path("<int:tournament_id>/admin/<int:draft_id>/~sync", views.sync, name="sync"),
    path("<int:tournament_id>/admin/<int:draft_id>/~finish", views.finish_round, name="finish_round"),
    path("game-results/", views.game_results, name="game_results"),
    path("report-result/", views.report_result, name="report_result"),
    path("confirm-result/", views.confirm_result, name="confirm_result"),
    path(
        "<int:tournament_id>/current-draft/", views.current_draft, name="current_draft"
    ),
    path("<int:tournament_id>/current-game/", views.current_game, name="current_game"),
    path(
        "<int:tournament_id>/my-current-match/",
        views.my_current_match,
        name="my_current_match",
    ),
    path(
        "<int:tournament_id>/draft/<int:draft_id>/standings/",
        views.standings,
        name="standings",
    ),
    path("<int:tournament_id>/enroll/", views.enroll_view, name="enroll_view"),
    path(
        "<int:tournament_id>/enroll-user/",
        views.enroll_user_view,
        name="enroll_user_view",
    ),
    path("all-events/", views.all_events, name="all_events"),
    path("my-events/", views.my_events, name="my_events"),
]
