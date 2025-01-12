from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import redirect

from .. import queries, services
from ..forms import ReportResultForm, ConfirmResultForm

User = get_user_model()


class AdminDataMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return JsonResponse({"error": "Insufficient authentication level"}, status=403)


class ConfirmResultView(FormView, LoginRequiredMixin):
    form_class = ConfirmResultForm
    template_name = "tournaments/current_draft.html"

    def get_success_url(self):
        return reverse_lazy("tournaments:draft_dashboard", kwargs=self.kwargs)

    def form_valid(self, form):
        match_id = form.cleaned_data["confirm_match_id"]
        match = queries.get_match(match_id)

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
        match = queries.get_match(match_id)
        services.report_result(
            match,
            player1_wins,
            player2_wins,
            reporting_player=player,
            admin=False,
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "Error: Please enter a valid game result.")
        return redirect(reverse_lazy("tournaments:draft_dashboard", kwargs=self.kwargs))


class AdminReportResultView(FormView, AdminDataMixin):
    form_class = ReportResultForm
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard",
            kwargs={
                "slug": self.kwargs["slug"],
                "draft_slug": self.kwargs["draft_slug"],
            },
        )

    def form_valid(self, form):
        match_id = form.cleaned_data["match_id"]
        player1_wins = form.cleaned_data["player1_wins"]
        player2_wins = form.cleaned_data["player2_wins"]
        match = queries.get_match(match_id)
        services.report_result(
            match,
            player1_wins,
            player2_wins,
            reporting_player=None,
            admin=True,
        )
        services.finish_match(match)
        return super().form_valid(form)


class AdminConfirmResultView(FormView, LoginRequiredMixin):
    form_class = ConfirmResultForm
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard",
            kwargs={
                "slug": self.kwargs["slug"],
                "draft_slug": self.kwargs["draft_slug"],
            },
        )

    def form_valid(self, form):
        match_id = form.cleaned_data["match_id"]

        match = queries.get_match(match_id)

        if match:
            services.finish_match(match)
            return redirect(self.get_success_url())
        else:
            return JsonResponse({"error": "Game not found"}, status=404)


class SeatDraftView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard",
            kwargs={
                "slug": self.kwargs["slug"],
                "draft_slug": self.kwargs["draft_slug"],
            },
        )

    def post(self, request, *args, **kwargs):
        slug = kwargs.get("draft_slug")
        draft = queries.get_draft(slug=slug)
        if not draft.seated:
            services.seat_draft(draft)
        return redirect(self.get_success_url())


class PairRoundView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard",
            kwargs={
                "slug": self.kwargs["slug"],
                "draft_slug": self.kwargs["draft_slug"],
            },
        )

    def post(self, request, *args, **kwargs):
        slug = kwargs.get("draft_slug")
        draft = queries.get_draft(slug=slug)
        services.pair_round_new(draft)
        return redirect(self.get_success_url())


class FinishRoundView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard",
            kwargs={
                "slug": self.kwargs["slug"],
                "draft_slug": self.kwargs["draft_slug"],
            },
        )

    def post(self, request, *args, **kwargs):
        slug = kwargs.get("draft_slug")
        draft = queries.get_draft(slug=slug)
        current_rd = queries.current_round(draft, force_update=True)
        services.finish_draft_round(current_rd)
        return redirect(self.get_success_url())


class ResetDraftView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard",
            kwargs={
                "slug": self.kwargs["slug"],
                "draft_slug": self.kwargs["draft_slug"],
            },
        )

    def post(self, request, *args, **kwargs):
        slug = kwargs.get("draft_slug")
        draft = queries.get_draft(slug=slug)
        services.clear_histories(draft)
        return redirect(self.get_success_url())


class FinishEventRoundView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_dashboard.html"

    def get_success_url(self):
        return reverse_lazy("tournaments:admin_dashboard", kwargs=self.kwargs)

    def post(self, request, *args, **kwargs):
        event_id = request.POST.get("finish-event-round")
        event = queries.get_tournament(id=event_id)

        services.finish_event_round(event)

        return redirect(self.get_success_url())


class StartPhaseView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_dashboard.html"

    def get_success_url(self):
        return reverse_lazy("tournaments:admin_dashboard", kwargs=self.kwargs)

    def post(self, request, *args, **kwargs):
        tournament_id = request.POST.get("start-phase")
        tournament = queries.get_tournament(id=tournament_id)

        phase_idx = tournament.current_round // 3 + 1
        phase = queries.get_phase_by_index(tournament, phase_idx)

        phase.started = True
        phase.save()

        return redirect(self.get_success_url())


class ResetEventView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_dashboard", kwargs={"slug": self.kwargs["slug"]}
        )

    def post(self, request, *args, **kwargs):
        event_id = request.POST.get("reset-event")
        event = queries.get_tournament(id=event_id)

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


class AdminEnrollUserView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_tournament_players.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_player_list", kwargs={"slug": self.kwargs["slug"]}
        )

    def post(self, request, *args, **kwargs):
        user_id = request.POST.get("user-id")
        user = User.objects.get(id=int(user_id))
        tournament_slug = kwargs["slug"]
        tournament = queries.get_tournament(slug=tournament_slug)

        try:
            services.enroll_for_event(user, tournament)
            messages.success(
                request,
                f"{user.name} was successfully registered for {tournament.name}!",
            )
        except ValueError as e:
            messages.error(request, f"Error: {e}")

        return redirect(self.get_success_url())
