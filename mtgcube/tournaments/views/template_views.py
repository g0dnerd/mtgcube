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
    ResetEventView,
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
            events = queries.enrolled_tournaments(None, force_update=True)
            status = {}
            for e in events:
                status[e.id] = True
            queryset = {"events": events, "status": status}
            return queryset
        
        player = queries.get_player(user)
        events = queries.enrolled_tournaments(player, force_update=True)
        if not events:
            return None

        status = {}
        for e in events:
            current_enroll = queries.enrollment_from_tournament(e, player)
            status[e.id] = current_enroll.registration_finished

            queryset = {"events": events, "status": status}

        return queryset


class AvailableEvents(LoginRequiredMixin, ListView):
    model = Tournament
    context_object_name = "tournaments"
    template_name = "tournaments/available_events.html"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return queries.available_tournaments(None, force_update=True)
        player = queries.get_player(user)
        available = queries.available_tournaments(player, force_update=True)
        enrolled = queries.enrolled_tournaments(player, force_update=True)

        status = {}
        for e in enrolled:
            current_enroll = queries.enrollment_from_tournament(e, player)
            status[e.id] = current_enroll.registration_finished

        queryset = {
            "enrolled": enrolled,
            "available": available,
            "status": status,
        }
        return queryset

    def post(self, request, *args, **kwargs):
        return EventEnrollView.as_view()(request, *args, **kwargs)


class AdminDraftDashboardView(AdminTemplateMixin, View):
    def get(self, request, *args, **kwargs):
        draft = queries.get_draft(slug=kwargs["draft_slug"])
        
        current_round = queries.admin_round_prefetch(draft, force_update=True)
        if current_round:
            matches = current_round.game_set.select_related(
                "player1__player__user", "player2__player__user"
            ).order_by("table")
            bye = queries.bye_this_round(draft)
            if bye:
                bye = bye.player.user.name

            m_ids = [m.id for m in matches]
            forms = {
                match_id: ReportResultForm(initial={"match_id": match_id})
                for match_id in m_ids
            }
        else:  # If no rounds exist yet in the current draft
            m_ids = []
            forms = []
            bye = False

        return render(
            request,
            "tournaments/admin_draft_dashboard.html",
            {
                "tournament_slug": kwargs["slug"],
                "draft": draft,
                "match_ids": m_ids,
                "bye": bye,
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

        drafts = queries.active_drafts_for_tournament(tournament)
        if drafts:
            draft_ids = [d.id for d in drafts]
            slugs = {d.id: d.slug for d in drafts}
        else:
            draft_ids = []
            drafts = None
            slugs = {}

        return render(
            request,
            "tournaments/admin_dashboard.html",
            {"tournament": tournament, "draft_ids": draft_ids, "slugs": slugs},
        )

    def post(self, request, *args, **kwargs):
        if 'finish-event-round' in request.POST:
            return FinishEventRoundView.as_view()(request, *args, **kwargs)
        if 'reset-event' in request.POST:
            return ResetEventView.as_view()(request, *args, **kwargs)


class IndexView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect("tournaments:tournament_list")


class DraftDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        tournament = queries.get_tournament(tournament_slug=kwargs["slug"])
        bye = False
        player = queries.get_player(user)
        current_enroll = queries.enrollment_from_tournament(tournament, player)
        if current_enroll.bye_this_round:
            bye = True
            form = None
            confirm_form = None
        draft = queries.get_draft(slug=kwargs["draft_slug"])

        current_round = queries.current_round(draft, force_update=True)
        if not current_round or current_round.finished:
            current_round = None
            match = None
            form = None
            confirm_form = None
        else:
            match = queries.current_match(current_enroll, current_round)
            if not bye:
                form = ReportResultForm(initial={"match_id": match.id})
                confirm_form = ConfirmResultForm(initial={"confirm_match_id": match.id})

        context={
                "draft": draft,
                "tournament": tournament,
                "round": current_round,
                "bye": bye,
                "match": match,
                "form": form,
                "confirm_form": confirm_form,
            }
        
        print(context)

        return render(
            request,
            "tournaments/current_draft.html",
            context,
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

        tournament = queries.get_tournament(tournament_slug=kwargs["slug"])
        player = queries.get_player(user)
        enrollment = queries.enrollment_from_tournament(tournament, player)
        if not enrollment:
            messages.error(
                request,
                "Error: You are not enrolled in this event.",
            )
            return redirect("tournaments:index")
        
        draft = queries.current_draft(enrollment)

        context = {"tournament": tournament, "draft": draft}
        return render(request, "tournaments/event_dashboard.html", context)


class MyPoolCheckinView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        tournament = queries.get_tournament(tournament_slug=kwargs["slug"])
        current_draft = queries.get_draft(slug=kwargs['draft_slug'])
        if not current_draft:
            messages.error(request, "No draft.")
            return redirect("tournaments:index")

        images = queries.images(user, current_draft, checkin=True)

        return render(
            request,
            "tournaments/my_pool_checkin.html",
            {"images": images, "tournament": tournament, "draft": current_draft},
        )


class MyPoolCheckoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        tournament = queries.get_tournament(tournament_slug=kwargs["slug"])
        current_draft = queries.get_draft(slug=kwargs['draft_slug'])
        if not current_draft:
            messages.error(request, "No draft.")
            return redirect("tournaments:index")

        images = queries.images(user, current_draft, checkin=False)

        return render(
            request,
            "tournaments/my_pool_checkout.html",
            {"images": images, "tournament": tournament, "draft": current_draft},
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
