from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.list import ListView
from django.urls import reverse_lazy

from .form_views import (
    SeatDraftView,
    PairRoundView,
    FinishRoundView,
    ResetDraftView,
    AdminReportResultView,
    FinishEventRoundView,
    SideEventEnrollView
)
from .. import queries as queries
from ..models import Tournament
from ..forms import ReportResultForm


class AdminTemplateMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to access this page.")
        return redirect("tournaments:index")


class EventListView(LoginRequiredMixin, ListView):
    model = Tournament
    context_object_name = "tournaments"
    template_name = "tournaments/tournament_list.html"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Tournament.objects.all()
        player = queries.player(user)
        return queries.all_tournaments(player, user.id)


class AdminDraftDashboardView(AdminTemplateMixin, View):
    def get(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        draft = queries.admin_draft_prefetch(slug, force_update=True)
        try:
            current_round = queries.admin_round_prefetch(draft, force_update=True)
            matches = current_round.game_set.select_related(
                "player1__player__user", "player2__player__user"
            ).order_by("table")

            m_ids = [m.id for m in matches]
            forms = {
                match_id: ReportResultForm(initial={"match_id": match_id})
                for match_id in m_ids
            }
        except ValueError: # If no rounds exist yet in the current draft
            m_ids = []
            forms = []

        return render(
            request,
            "tournaments/admin_draft_dashboard.html",
            {"draft_id": draft.id, "match_ids": m_ids, "forms": forms},
        )

    def post(self, request, *args, **kwargs):
        if "match_id" in request.POST:
            return AdminReportResultView.as_view()(request, *args, **kwargs)
        if "seat-draft" in request.POST:
            return SeatDraftView.as_view()(request, *args, **kwargs)
        if "pair-round" in request.POST:
            return PairRoundView.as_view()(request, *args, **kwargs)
        if "finish-round" in request.POST:
            return FinishRoundView.as_view()(request, *args, **kwargs)
        if "reset-draft" in request.POST:
            return ResetDraftView.as_view()(request, *args, **kwargs)


class AdminDashboardView(AdminTemplateMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
        try:
            drafts = queries.active_drafts_for_event(tournament)
            draft_ids = [d.id for d in drafts]
            slugs = {d.id: d.slug for d in drafts}
        except ValueError:
            draft_ids = []
            drafts = None
            slugs = {}

        return render(
            request,
            "tournaments/admin_dashboard.html",
            {"tournament": tournament, "draft_ids": draft_ids, "slugs": slugs},
        )

    def post(self, request, *args, **kwargs):
        return FinishEventRoundView.as_view()(request, *args, **kwargs)


class IndexView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect('tournaments:tournament_list')


class DraftDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
        try:
            player = queries.player(user)
            current_enroll = queries.enrollment_from_tournament(tournament, player)
            draft = queries.current_draft(current_enroll, user.id)
        except ValueError:
            messages.error(
                request,
                "You must be registered in a tournament to access the event dashboard.\
                If you believe you should be, please contact on of our staff members.",
            )
            return redirect("tournaments:index")

        return render(
            request, "tournaments/current_draft.html", context={"draft": draft, "tournament": tournament}
        )


class EventDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            return redirect(reverse_lazy("tournaments:admin_dashboard", kwargs=kwargs))

        try:
            player = queries.player(user)
        except ValueError:
            messages.error(
                request,
                "There is an issue with your account. Please contact one of our event administrators.\
                (ERR:NO_PLAYER_FOR_USER)",
            )
            return redirect("tournaments:index")

        tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
        try:
            tournament.tournament
            side_events = []
            is_side = True
        except AttributeError:
            try:
                side_events = list(
                    queries.available_side_events(
                        player, tournament, user.id, force_update=True
                    )
                )
            except ValueError:
                side_events = []
            is_side = False

        context = {
            "tournament": tournament,
            "side_events": side_events,
            "is_side": is_side,
        }
        return render(request, "tournaments/event_dashboard.html", context)

    def post(self, request, *args, **kwargs):
        return SideEventEnrollView.as_view()(request, *args, **kwargs)


class MyPoolCheckinView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        tournament = queries.get_tournament(tournament_slug=kwargs['slug'])

        try:
            player = queries.player(user)
            current_enroll = queries.enrollment_from_tournament(tournament, player)
            current_draft = queries.current_draft(current_enroll, user.id)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("tournaments:index")

        images = queries.images(user, current_draft, checkin=True)

        return render(
            request,
            "tournaments/my_pool_checkin.html",
            {"images": images, "tournament": tournament},
        )


class MyPoolCheckoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        tournament = queries.get_tournament(tournament_slug=kwargs['slug'])

        try:
            player = queries.player(user)
            current_enroll = queries.enrollment_from_tournament(tournament, player)
            current_draft = queries.current_draft(current_enroll, user.id)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("tournaments:index")

        images = queries.images(user, current_draft, checkin=False)

        return render(
            request,
            "tournaments/my_pool_checkout.html",
            {"images": images, "tournament": tournament},
        )
