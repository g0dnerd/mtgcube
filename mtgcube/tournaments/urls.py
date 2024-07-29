from django.urls import path

from .views import admin_data_views as admin
from .views import player_data_views as player
from .views import generic_data_views as generic
from .views import template_views as templates

app_name = "tournaments"

urlpatterns = [
    path("", templates.EventListView.as_view(), name="index"),
    path("tournament-list/", templates.EventListView.as_view(), name="tournament_list"),
    path("event-dashboard/<slug:slug>/", templates.EventDashboardView.as_view(), name="event_dashboard"),
    path("admin-dashboard/<slug:slug>/", templates.AdminDashboardView.as_view(), name="admin_dashboard"),
    path("admin-draft-test/<int:draft_id>/", templates.AdminDraftDashboardView.as_view(), name="admin_draft_test"),
    path("admin-dashboard/<slug:slug>", templates.AdminDraftDashboardView.as_view(), name="admin_draft_dashboard"),
    path("event-dashboard/<slug:slug>/my-current-draft/", templates.DraftDashboardView.as_view(), name="draft_dashboard"),
    path("event-dashboard/<slug:slug>/my-current-draft/check-in/", player.CheckinView.as_view(), name="checkin"),
    path("event-dashboard/<slug:slug>/my-current-draft/check-out/", player.CheckoutView.as_view(), name="checkout"),
    path("event-dashboard/<slug:slug>/my-current-draft/deck-upload/", templates.MyPoolCheckinView.as_view(), name="my_pool_checkin"),
    path("event-dashboard/<slug:slug>/my-current-draft/deck-upload/", templates.MyPoolCheckoutView.as_view(), name="my_pool_checkout"),
    path("event-dashboard/<slug:slug>/my-current-draft/my-pool-check-in/<int:image_id>/~checkindelete/", player.DeleteImageCheckinView.as_view(), name="delete_image_checkin"),
    path("event-dashboard/<slug:slug>/my-current-draft/my-pool-check-out/<int:image_id>/~checkoutdelete/", player.DeleteImageCheckoutView.as_view(), name="delete_image_checkout"),
    path("event-dashboard/<int:tournament_id>/~player-basic-info/", player.PlayerBasicInfoView.as_view(), name="player_basic_info"),
    path("event-dashboard/<int:tournament_id>/~player-draft-info/", player.PlayerDraftInfoView.as_view(), name="player_draft_info"),
    path("event-dashboard/<int:tournament_id>/~announcement/", player.AnnouncementView.as_view(), name="announcement"),
    path("draft/<int:draft_id>/~player-match-info/", player.PlayerMatchInfoView.as_view(), name="player_match_info"),
    path("draft/<int:draft_id>/~player-pairings-info/", player.PlayerOtherPairingsInfoView.as_view(), name="player_pairings_info"),
    path("draft/<int:draft_id>/~draft-standings/", generic.DraftStandingsView.as_view(), name="draft_standings"),
    path("draft/<int:draft_id>/~seatings/", generic.SeatingsView.as_view(), name="seatings"),
    path("draft/<int:draft_id>/~players/", generic.PlayerListView.as_view(), name="draft_players"),
    path("draft/<int:draft_id>/~report-result/", player.ReportResultView.as_view(), name="report_result"),
    path("draft/<int:draft_id>/~confirm-result/", player.ConfirmResultView.as_view(), name="confirm_result"),
    path("event-dashboard/<int:tournament_id>/~timetable/", player.TimetableView.as_view(), name="timetable"),
    path("event-dashboard/<int:tournament_id>/~standings/", generic.EventStandingsView.as_view(), name="event_standings"),
    path("admin-dashboard/~draft/<int:draft_id>/", admin.AdminDraftInfoEmbedView.as_view(), name="admin_draft_embed"),
    path("admin-dashboard/~match/<int:match_id>", admin.AdminMatchInfoEmbedView.as_view(), name="admin_match_embed"),
]