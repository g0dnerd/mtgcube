from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.urls import reverse_lazy

from .form_views import (
    SeatDraftView,
    PairRoundView,
    FinishRoundView,
    ResetDraftView,
    AdminReportResultView,
    PlayerReportResultView,
    FinishEventRoundView,
    ConfirmResultView,
    EventEnrollView,
)
from .. import queries as queries
from ..models import Tournament, Cube
from ..forms import ReportResultForm, ConfirmResultForm


class AdminTemplateMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to access this page.")
        return redirect("tournaments:index")


class MyEventsView(LoginRequiredMixin, ListView):
    model = Tournament
    context_object_name = "tournaments"
    template_name = "tournaments/tournament_list.html"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            events = queries.enrolled_tournaments(None, user.id, force_update=True)
            status = {}
            for e in events:
                status[e.id] = True
            queryset = {"events": events, "status": status}
            return queryset
        try:
            player = queries.player(user)
            events = queries.enrolled_tournaments(player, user.id, force_update=True)
            status = {}
            for e in events:
                current_enroll = queries.enrollment_from_tournament(e, player)
                status[e.id] = current_enroll.registration_finished

            queryset = {"events": events, "status": status}

        except ValueError:
            return None
        return queryset


class AvailableEvents(LoginRequiredMixin, ListView):
    model = Tournament
    context_object_name = "tournaments"
    template_name = "tournaments/available_events.html"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return queries.available_tournaments(None, user.id, force_update=True)
        player = queries.player(user)
        try:
            available = queries.available_tournaments(
                player, user.id, force_update=True
            )
            enrolled = queries.enrolled_tournaments(player, user.id, force_update=True)

            status = {}
            for e in enrolled:
                current_enroll = queries.enrollment_from_tournament(e, player)
                status[e.id] = current_enroll.registration_finished

            queryset = {
                "enrolled": enrolled,
                "available": available,
                "status": status,
            }
        except ValueError:
            return None
        return queryset

    def post(self, request, *args, **kwargs):
        return EventEnrollView.as_view()(request, *args, **kwargs)


class AdminDraftDashboardView(AdminTemplateMixin, View):
    def get(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        draft = queries.get_draft(slug=slug, force_update=True)
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
        except ValueError:  # If no rounds exist yet in the current draft
            m_ids = []
            forms = []

        return render(
            request,
            "tournaments/admin_draft_dashboard.html",
            {
                "tournament_slug": slug,
                "draft_id": draft.id,
                "match_ids": m_ids,
                "forms": forms,
            },
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
        tournament = queries.get_tournament(tournament_slug=kwargs["slug"])
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
        return redirect("tournaments:tournament_list")


class DraftDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        tournament = queries.get_tournament(tournament_slug=kwargs["slug"])
        bye = False
        player = queries.player(user)
        current_enroll = queries.enrollment_from_tournament(tournament, player)
        if current_enroll.bye_this_round:
            bye = True
        draft = queries.current_draft(current_enroll, user.id)

        current_round = queries.current_round(draft, force_update=True)
        match = queries.current_match(
            current_enroll, current_round, user.id, force_update=True
        )

        if not match:
            current_round = None
            match = None
            form = None
            confirm_form = None
        else:
            form = ReportResultForm(initial={"match_id": match.id})
            confirm_form = ConfirmResultForm(initial={"confirm_match_id": match.id})


        return render(
            request,
            "tournaments/current_draft.html",
            context={
                "draft": draft,
                "tournament": tournament,
                "round": current_round,
                "bye": bye,
                "match": match,
                "form": form,
                "confirm_form": confirm_form,
            },
        )
    
    def post(self, request, *args, **kwargs):
        if "match_id" in request.POST:
            return PlayerReportResultView.as_view()(request, *args, **kwargs)
        if "confirm_match_id" in request.POST:
            return ConfirmResultView.as_view()(request, *args, **kwargs)


class EventDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            return redirect(reverse_lazy("tournaments:admin_dashboard", kwargs=kwargs))

        try:
            queries.player(user)
        except ValueError:
            messages.error(
                request,
                "There is an issue with your account. Please contact one of our event administrators.\
                (ERR:NO_PLAYER_FOR_USER)",
            )
            return redirect("tournaments:index")

        tournament = queries.get_tournament(tournament_slug=kwargs["slug"])

        context = {"tournament": tournament}
        return render(request, "tournaments/event_dashboard.html", context)


class MyPoolCheckinView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        tournament = queries.get_tournament(tournament_slug=kwargs["slug"])

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
        tournament = queries.get_tournament(tournament_slug=kwargs["slug"])

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


class CubeDetailView(LoginRequiredMixin, DetailView):
    model = Cube
    context_object_name = "cube"
    template_name = "tournaments/cube_detail.html"

    def get_context_data(self, **kwargs):
        from .player_data_views import PRONOUN_CHOICES
        context = super().get_context_data(**kwargs)
        context["creator_pronouns"] = PRONOUN_CHOICES[context['object'].creator.pronouns]
        return context
