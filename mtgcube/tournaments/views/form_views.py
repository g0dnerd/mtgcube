from django.contrib import messages
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import redirect

from .. import queries, services
from ..forms import ReportResultForm, ConfirmResultForm


class AdminDataMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return JsonResponse({"error": "Insufficient authentication level"}, status=403)


class ConfirmResultView(FormView, LoginRequiredMixin):
    form_class = ConfirmResultForm
    template_name = "tournaments/current_draft.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:draft_dashboard", kwargs=self.kwargs
        )

    def form_valid(self, form):
        match_id = form.cleaned_data["confirm_match_id"]

        match = queries.match_from_id(match_id)

        if match:
            services.finish_match(match)
            return redirect(self.get_success_url())
        else:
            return JsonResponse({"error": "Game not found"}, status=404)


class PlayerReportResultView(FormView, LoginRequiredMixin):
    form_class = ReportResultForm
    template_name = "tournaments/current_draft.html"

    def get_success_url(self):
        return reverse_lazy("tournaments:draft_dashboard", kwargs=self.kwargs)

    def form_valid(self, form):
        match_id = form.cleaned_data["match_id"]
        player1_wins = form.cleaned_data["player1_wins"]
        player2_wins = form.cleaned_data["player2_wins"]
        player = queries.get_player(self.request.user)
        match = queries.match_from_id(match_id)
        try:
            services.report_result(
                match,
                player1_wins,
                player2_wins,
                reporting_player=player,
                admin=False,
            )
            return redirect(self.get_success_url())
        except ValueError as e:
            return JsonResponse({"error": str(e)})


class AdminReportResultView(FormView, AdminDataMixin):
    form_class = ReportResultForm
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard", kwargs={"slug": self.kwargs["slug"], "draft_slug": self.kwargs["draft_slug"]}
        )

    def form_valid(self, form):
        match_id = form.cleaned_data["match_id"]
        player1_wins = form.cleaned_data["player1_wins"]
        player2_wins = form.cleaned_data["player2_wins"]
        match = queries.match_from_id(match_id)
        services.report_result(
            match,
            player1_wins,
            player2_wins,
            reporting_player=None,
            admin=True,
        )
        services.finish_match(match)
        return super().form_valid(form)


class SeatDraftView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard", kwargs={"slug": self.kwargs["slug"], "draft_slug": self.kwargs["draft_slug"]}
        )

    def post(self, request, *args, **kwargs):
        slug = kwargs.get("draft_slug")
        draft = queries.get_draft(slug=slug, force_update=True)
        if not draft.seated:
            services.seat_draft(draft)
        return redirect(self.get_success_url())


class PairRoundView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard", kwargs={"slug": self.kwargs["slug"], "draft_slug": self.kwargs["draft_slug"]}
        )

    def post(self, request, *args, **kwargs):
        slug = kwargs.get("draft_slug")
        draft = queries.get_draft(slug=slug, force_update=True)
        services.pair_round_new(draft)
        return redirect(self.get_success_url())


class FinishRoundView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard", kwargs={"slug": self.kwargs["slug"], "draft_slug": self.kwargs["draft_slug"]}
        )

    def post(self, request, *args, **kwargs):
        slug = kwargs.get("draft_slug")
        draft = queries.get_draft(slug=slug, force_update=True)
        current_rd = queries.current_round(draft, force_update=True)
        services.finish_draft_round(current_rd)
        return redirect(self.get_success_url())


class ResetDraftView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard", kwargs={"slug": self.kwargs["slug"], "draft_slug": self.kwargs["draft_slug"]}
        )

    def post(self, request, *args, **kwargs):
        slug = kwargs.get("draft_slug")
        draft = queries.get_draft(slug=slug, force_update=True)
        services.clear_histories(draft)
        return redirect(self.get_success_url())


class FinishEventRoundView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_dashboard", kwargs=self.kwargs
        )

    def post(self, request, *args, **kwargs):
        print(request.POST)
        event_id = request.POST.get("finish-event-round")
        print(f'Event ID: {event_id}')
        event = queries.get_tournament(tournament_id=event_id)

        services.finish_event_round(event)

        return redirect(self.get_success_url())


class ResetEventView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_dashboard", kwargs={"slug": self.kwargs["slug"]}
        )

    def post(self, request, *args, **kwargs):
        event_id = request.POST.get("reset-event")
        event = queries.get_tournament(tournament_id=event_id)

        services.reset_tournament(event)

        return redirect(self.get_success_url())


class EventEnrollView(FormView, LoginRequiredMixin):
    template_name = "tournaments/tournament_list.html"
    success_url = reverse_lazy("tournaments:index")

    def post(self, request, *args, **kwargs):
        event_id = request.POST.get("event-id")
        tournament = queries.get_tournament(id=int(event_id))
        try:
            services.enroll_for_event(request.user, tournament)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("tournaments:registration")

        messages.success(request, f"You successfully registered for {tournament.name}!")

        return redirect(self.get_success_url())
