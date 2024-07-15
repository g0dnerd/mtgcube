from django.urls import path

# 1from django.views.generic import RedirectView
from . import views

app_name = "tournaments"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:game_id>/~match-info", views.game_by_id, name="game_by_id"),
    path("~report-result", views.report_result, name="report_result"),
    path("~confirm-result", views.confirm_result, name="confirm_result"),
    path("my-events/", views.my_events, name="my_events"),
    path("<int:tournament_id>/", views.tournament_view, name="tournament_view"),
    path("<int:tournament_id>/~current-match", views.current_match, name="current_match"),
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
        views.clear_history,
        name="clear_history",
    ),
    path("<int:tournament_id>/admin/<int:draft_id>/~sync", views.sync, name="sync"),
    path("<int:tournament_id>/admin/<int:draft_id>/~finish", views.finish_round, name="finish_round"),
    path("<int:tournament_id>/admin/<int:draft_id>/~seatings", views.seat_draft, name="seat_draft"),
    path("<int:tournament_id>/admin/<int:draft_id>/~status", views.round_status, name="round_status"),
    path(
        "<int:tournament_id>/admin/draft/<int:draft_id>/~start",
        views.start_round,
        name="start_round",
    ),
    path(
        "<int:tournament_id>/admin/draft/<int:draft_id>/~stop",
        views.finish_round,
        name="stop_round",
    ),
    path(
        "<int:tournament_id>/draft/<int:draft_id>/",
        views.current_draft_view,
        name="current_draft_view",
    ),
    path("<int:tournament_id>/draft/<int:draft_id>/~standings", views.draft_standings, name="draft_standings"),
    path("<int:tournament_id>/draft/<int:draft_id>/~seatings", views.seatings, name="seatings"),
    path(
        "<int:tournament_id>/draft/<int:draft_id>/~draftinfo", views.current_draft, name="current_draft"
    ),
]
