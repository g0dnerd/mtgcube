from django.contrib import messages
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import redirect

from .. import queries, services
from ..forms import ReportResultForm


class AdminDataMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return JsonResponse({"error": "Insufficient authentication level"}, status=403)


class AdminReportResultView(FormView, AdminDataMixin):
    form_class = ReportResultForm
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard", kwargs={"slug": self.kwargs["slug"]}
        )

    def form_valid(self, form):
        match_id = form.cleaned_data["match_id"]
        player1_wins = form.cleaned_data["player1_wins"]
        player2_wins = form.cleaned_data["player2_wins"]
        try:
            queries.report_result(
                match_id,
                player1_wins,
                player2_wins,
                reporting_player=None,
                admin=True,
            )
            return super().form_valid(form)
        except ValueError as e:
            return JsonResponse({"error": str(e)})


class SeatDraftView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard", kwargs={"slug": self.kwargs["slug"]}
        )

    def post(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        draft = queries.admin_draft_prefetch(slug, force_update=True)
        if not draft.seated:
            services.seatings(draft)
        return redirect(self.get_success_url())


class PairRoundView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard", kwargs={"slug": self.kwargs["slug"]}
        )

    def post(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        draft = queries.admin_draft_prefetch(slug, force_update=True)
        current_rd = queries.current_round(draft, force_update=True)
        services.pair_round(current_rd)
        return redirect(self.get_success_url())


class FinishRoundView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard", kwargs={"slug": self.kwargs["slug"]}
        )

    def post(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        draft = queries.admin_draft_prefetch(slug, force_update=True)
        current_rd = queries.current_round(draft, force_update=True)
        services.finish_round(current_rd)
        return redirect(self.get_success_url())


class ResetDraftView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_draft_dashboard.html"

    def get_success_url(self):
        return reverse_lazy(
            "tournaments:admin_draft_dashboard", kwargs={"slug": self.kwargs["slug"]}
        )

    def post(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        draft = queries.admin_draft_prefetch(slug, force_update=True)
        services.clear_histories(draft)
        return redirect(self.get_success_url())


class FinishEventRoundView(FormView, AdminDataMixin):
    template_name = "tournaments/admin_dashboard.html"
    success_url = reverse_lazy("tournaments:admin_dashboard")

    def post(self, request, *args, **kwargs):
        event_id = request.POST.get("finish-event-round")
        event = queries.get_tournament(event_id)

        event.current_round += 1
        event.save()
        return redirect(self.get_success_url())

class SideEventEnrollView(FormView, LoginRequiredMixin):
    template_name = "tournaments/event_dashboard.html"
    success_url = reverse_lazy("tournaments:event_dashboard")

    def get_success_url(self):
        return reverse_lazy("tournaments:event_dashboard", kwargs=self.kwargs)
    
    def post(self, request, *args, **kwargs):
        event_id = request.POST.get("event-id")
        side_event = queries.get_tournament(int(event_id))
        try:
            queries.enroll_for_side_event(request.user, side_event)
            player = queries.player(request.user)
            all_enrollments = queries.all_enrollments(
                player, request.user.id, force_update=True
            )
            queries.current_enrollment(
                all_enrollments, request.user.id, force_update=True
            )

            messages.success(
                request, f"You successfully registered for {side_event.name}!"
            )

            return redirect(self.get_success_url())
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("tournaments:index")