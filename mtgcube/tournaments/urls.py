from django.urls import path

from .views import admin_data_views as admin_data_views
from .views import player_data_views as player_data_views
from .views import template_views as template_views

app_name = "tournaments"

urlpatterns = [
    path("", template_views.IndexView.as_view(), name="index"),
    path("event-dashboard/", template_views.EventDashboardView.as_view(), name="event_dashboard"),
    path("admin-dashboard/", template_views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path("admin-dashboard/<int:tournament_id>/draft/<int:draft_id>/", template_views.AdminDraftDashboardView.as_view(), name="admin_draft_dashboard"),
    path("event-dashboard/draft/", template_views.DraftDashboardView.as_view(), name="draft_dashboard"),
    path("event-dashboard/draft/check-in/", player_data_views.checkin, name="checkin"),
    path("event-dashboard/draft/check-out/", player_data_views.checkout, name="checkout"),
    path("event-dashboard/draft/my-pool-check-in/", template_views.MyPoolCheckinView.as_view(), name="my_pool_checkin"),
    path("event-dashboard/draft/my-pool-check-out/", template_views.MyPoolCheckoutView.as_view(), name="my_pool_checkout"),
    path("event-dashboard/draft/my-pool-check-in/<int:image_id>/~delete/", player_data_views.delete_image_checkin, name="delete_image_checkin"),
    path("event-dashboard/draft/my-pool-check-out/<int:image_id>/~delete/", player_data_views.delete_image_checkin, name="delete_image_checkout"),
    path("event-dashboard/draft/my-pool-check-in/<int:image_id>/~replace/", player_data_views.replace_image_checkin, name="replace_image_checkin"),
    path("event-dashboard/draft/my-pool-check-out/<int:image_id>/~replace/", player_data_views.replace_image_checkout, name="replace_image_checkout"),
    path("event-dashboard/~announcement/", player_data_views.AnnouncementView.as_view(), name="announcement"),
    path("event-dashboard/~next-draft/", player_data_views.UpcomingDraftView.as_view(), name="next_draft"),
    path("admin-dashboard/~drafts/", admin_data_views.AdminDraftsView.as_view(), name="admin_drafts"),
    path("admin-dashboard/~standings/", player_data_views.PlayerEventStandingsView.as_view(), name="event_standings"),
    path("admin-dashboard/<int:draft_id>/~matches/", admin_data_views.AdminDraftInfoView.as_view(), name="admin_draft_info"),
    path("admin-dashboard/~pair/", admin_data_views.PairRoundView.as_view(), name="pair_round"),
    path("admin-dashboard/~reset/", admin_data_views.ClearHistoryView.as_view(), name="clear_history"),
    path("admin-dashboard/~seat/", admin_data_views.SeatDraftView.as_view(), name="seat_draft"),
    path("admin-dashboard/~finish/", admin_data_views.FinishRoundView.as_view(), name="finish_round"),
    path("admin-dashboard/<int:draft_id>/~status/", player_data_views.round_status, name="round_status"),
    path("admin-dashboard/<int:draft_id>/~start/", admin_data_views.StartRoundView.as_view(), name="start_round"),
    path("admin-dashboard/draft/~sync/", admin_data_views.SyncRoundView.as_view(), name="sync_round"),
    path("event-dashboard/draft/~player-basic-info/", player_data_views.PlayerBasicInfoView.as_view(), name="player_basic_info"),
    path("event-dashboard/draft/~player-draft-info/", player_data_views.PlayerDraftInfoView.as_view(), name="player_draft_info"),
    path("event-dashboard/draft/~player-match-info/", player_data_views.PlayerMatchInfoView.as_view(), name="player_match_info"),
    path("event-dashboard/draft/~player-pairings-info/", player_data_views.PlayerOtherPairingsInfoView.as_view(), name="player_pairings_info"),
    path("event-dashboard/draft/~player-seatings-info/", player_data_views.PlayerSeatingsView.as_view(), name="player_seatings_info"),
    path("event-dashboard/draft/~player-standings-info/", player_data_views.PlayerStandingsView.as_view(), name="player_standings_info"),
    path("~report-result/", player_data_views.ReportResultView.as_view(), name="report_result"),
    path("~confirm-result/", player_data_views.ConfirmResultView.as_view(), name="confirm_result"),
]