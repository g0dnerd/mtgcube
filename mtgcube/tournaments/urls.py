from django.urls import path

from .views import admin_data_views as admin
from .views import player_data_views as player
from .views import generic_data_views as generic
from .views import template_views as templates

app_name = "tournaments"

urlpatterns = [
  path("", templates.MyEventsView.as_view(), name="index"),
  path("registration/", templates.AvailableEvents.as_view(), name="available_events"),
  path("cube/<slug:slug>/", templates.CubeDetailView.as_view(), name="cube_detail"),
  path(
    "event-dashboard/<slug:slug>/",
    templates.EventDashboardView.as_view(),
    name="event_dashboard",
  ),
  path(
    "admin-dashboard/<slug:slug>/",
    templates.AdminDashboardView.as_view(),
    name="admin_dashboard",
  ),
  path(
    "admin-dashboard/<slug:slug>/player-list/",
    templates.AdminPlayerListView.as_view(),
    name="admin_player_list",
  ),
  path(
    "admin-dashboard/<slug:slug>/<slug:draft_slug>/",
    templates.AdminDraftDashboardView.as_view(),
    name="admin_draft_dashboard",
  ),
  path(
    "admin-dashboard/<slug:slug>/<slug:draft_slug>/~draft/",
    admin.AdminDraftInfoEmbedView.as_view(),
    name="admin_draft_embed",
  ),
  path(
    "admin-dashboard/<slug:slug>/~match/<int:match_id>/",
    admin.AdminMatchInfoEmbedView.as_view(),
    name="admin_match_embed",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/",
    templates.DraftDashboardView.as_view(),
    name="draft_dashboard",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/checkin-upload/",
    player.CheckinView.as_view(),
    name="checkin",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/checkout-upload/",
    player.CheckoutView.as_view(),
    name="checkout",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/checkin-pool/",
    templates.MyPoolCheckinView.as_view(),
    name="my_pool_checkin",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/checkout-pool/",
    templates.MyPoolCheckoutView.as_view(),
    name="my_pool_checkout",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/<int:image_id>/~checkindelete/",
    player.DeleteImageCheckinView.as_view(),
    name="delete_image_checkin",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/<int:image_id>/~checkoutdelete/",
    player.DeleteImageCheckoutView.as_view(),
    name="delete_image_checkout",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/~player-draft-info/",
    player.PlayerDraftInfoView.as_view(),
    name="player_draft_info",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/~player-basic-info/",
    player.PlayerBasicInfoView.as_view(),
    name="player_basic_info",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/<int:match_id>/~player-match/",
    player.PlayerFullMatchInfoView.as_view(),
    name="player_match_info",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/~player-pairings/",
    player.PlayerOtherPairingsInfoView.as_view(),
    name="player_pairings_info",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/~draft-standings/",
    generic.DraftStandingsView.as_view(),
    name="draft_standings",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/~seatings/",
    generic.SeatingsView.as_view(),
    name="seatings",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/~players/",
    generic.PlayerListView.as_view(),
    name="draft_players",
  ),
  path(
    "event-dashboard/<slug:slug>/<slug:draft_slug>/~player-match-preview/",
    player.PlayerPreviewMatchInfoView.as_view(),
    name="player_match_info_light",
  ),
  path(
    "event-dashboard/<slug:slug>/~timetable/",
    player.TimetableView.as_view(),
    name="timetable",
  ),
  path(
    "event-dashboard/<slug:slug>/~standings/",
    generic.EventStandingsView.as_view(),
    name="event_standings",
  ),
  path(
    "event-dashboard/<slug:slug>/~announcement/",
    player.AnnouncementView.as_view(),
    name="announcement",
  ),
]
