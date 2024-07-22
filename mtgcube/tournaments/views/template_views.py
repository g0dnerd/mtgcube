from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View, generic
from django.db.models import Q

from ..models import Enrollment, Image, Player, Tournament, Draft


class AdminDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            messages.error(
                request,
                "You must be an admin or staff member to access this page.",
            )
            return redirect("tournaments:index")

        t_id = cache.get("latest_tournament_id")
        if not t_id:
            t = Tournament.objects.all().order_by("-start_datetime").first()
            t_id = t.id
            cache.set("latest_tournament_id", t_id, 300)  # Cache for 5 minutes
        else:
            t = get_object_or_404(Tournament, pk=t_id)

        return render(
            request,
            "tournaments/admin_dashboard.html",
            context={"tournament_id": t_id, "tournament_name": str(t)},
        )


class IndexView(generic.ListView):
    template_name = "tournaments/index.html"
    context_object_name = "all_tournaments"

    def get_queryset(self):
        return Tournament.objects.all()


class AdminDraftDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            messages.error(
                request,
                "You must be an admin or staff member to access this page.",
            )
            return redirect("tournaments:dashboard")

        t_id = cache.get("latest_tournament_id")
        if not t_id:
            t = Tournament.objects.all().order_by("-start_datetime").first()
            t_id = t.id
            cache.set("latest_tournament_id", t_id, 300)  # Cache for 5 minutes
        else:
            t = get_object_or_404(Tournament, pk=t_id)

        t_id = self.kwargs["tournament_id"]

        d_id = self.kwargs["draft_id"]

        return render(
            request,
            "tournaments/admin_draft_dashboard.html",
            context={"tournament_id": t_id, "draft_id": d_id},
        )


class DraftDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        player = cache.get(f"player_{user.id}")
        if not player:
            try:
                player = Player.objects.get(user=user)
                cache.set(
                    f"player_{user.id}", player, 60
                )  # Cache player object for 1 minute
            except Player.DoesNotExist:
                messages.error(
                    request,
                    "You must be registered in a tournament to access the event dashboard.\nIf you believe you should be, please contact on of our staff members.",
                )
                return redirect("tournaments:index")

        current_draft = cache.get(f"draft_{player.id}")
        if not current_draft:
            enrollments = cache.get(f"enrollments_{player.id}")
            if not enrollments:
                enrollments = Enrollment.objects.filter(player=player)
                cache.set(
                    f"enrollments_{user.id}", enrollments, 300
                )  # Cache draft object for 5 minutes

            current_enroll = cache.get(f"current_enroll_{player.id}")
            if not current_enroll:
                current_enroll = enrollments.order_by("-enrolled_on").first()
                cache.set(
                    f"current_enroll_{player.id}", current_enroll, 300
                )  # Cache enrollments for 3 minutes

            current_draft = (
                Draft.objects.filter(
                    ~Q(finished=True), enrollments__in=[current_enroll]
                )
                .order_by("phase__phase_idx")
                .first()
            )
            cache.set(
                f"draft_{user.id}", current_draft, 120
            )  # Cache draft object for 2 minutes

        if not current_draft:
            messages.error(
                request,
                "You must be registered in a tournament to access the draft dashboard.\nIf you believe you should be, please contact on of our staff members.",
            )
            return redirect("tournaments:index")
        return render(request, "tournaments/current_draft.html")


class EventDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            return redirect("tournaments:admin_dashboard")

        player = cache.get(f"player_{user.id}")
        if not player:
            try:
                player = Player.objects.get(user=user)
                cache.set(
                    f"player_{user.id}", player, 60
                )  # Cache player object for 1 minute
            except Player.DoesNotExist:
                messages.error(
                    request,
                    "You must be registered in a tournament to access the event dashboard.\nIf you believe you should be, please contact on of our staff members.",
                )
                return redirect("tournaments:index")

        enrollments = cache.get(f"enrollments_{player.id}")
        if not enrollments:
            enrollments = Enrollment.objects.filter(player=player)
            cache.set(
                f"enrollments_{player.id}", enrollments, 60
            )  # Cache enrollments for 1 minute

        if not enrollments.exists():
            messages.error(
                request,
                "You must be registered in a tournament to access the event dashboard.\nIf you believe you should be, please contact on of our staff members.",
            )
            return redirect("tournaments:index")

        current_enrollment = cache.get(f"current_enroll_{player.id}")
        if not current_enrollment:
            current_enrollment = enrollments.order_by("-enrolled_on").first()
            cache.set(
                f"current_enroll_{player.id}", current_enrollment, 300
            )  # Cache enrollments for 5 minutes

        context = {
            "tournament": current_enrollment,
        }

        if not user.is_superuser:
            return render(request, "tournaments/event_dashboard.html", context)


class MyPoolCheckinView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        player = cache.get(f"player_{user.id}")
        if not player:
            try:
                player = Player.objects.get(user=user)
                cache.set(
                    f"player_{user.id}", player, 300
                )  # Cache player object for 5 minutes
            except Player.DoesNotExist:
                return redirect("tournaments:index")

        current_draft = cache.get(f"draft_{player.id}")
        if not current_draft:
            enrollments = cache.get(f"enrollments_{player.id}")
            if not enrollments:
                enrollments = Enrollment.objects.filter(player=player)
                cache.set(
                    f"enrollments_{user.id}", enrollments, 300
                )  # Cache draft object for 5 minutes

            current_enroll = cache.get(f"current_enroll_{player.id}")
            if not current_enroll:
                current_enroll = enrollments.order_by("-enrolled_on").first()
                cache.set(
                    f"current_enroll_{player.id}", current_enroll, 300
                )  # Cache enrollments for 3 minutes

            current_draft = (
                Draft.objects.filter(
                    ~Q(finished=True), enrollments__in=[current_enroll]
                )
                .order_by("phase__phase_idx")
                .first()
            )
            cache.set(
                f"draft_{user.id}", current_draft, 120
            )  # Cache draft object for 2 minutes

        images = Image.objects.filter(
            user=user, draft_idx=current_draft.id, checkin=True
        )
        print(images)
        return render(
            request,
            "tournaments/my_pool_checkin.html",
            {"images": images},
        )


class MyPoolCheckoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        player = cache.get(f"player_{user.id}")
        if not player:
            try:
                player = Player.objects.get(user=user)
                cache.set(
                    f"player_{user.id}", player, 300
                )  # Cache player object for 5 minutes
            except Player.DoesNotExist:
                return redirect("tournaments:index")

        current_draft = cache.get(f"draft_{player.id}")
        if not current_draft:
            enrollments = cache.get(f"enrollments_{player.id}")
            if not enrollments:
                enrollments = Enrollment.objects.filter(player=player)
                cache.set(
                    f"enrollments_{user.id}", enrollments, 300
                )  # Cache draft object for 5 minutes

            current_enroll = cache.get(f"current_enroll_{player.id}")
            if not current_enroll:
                current_enroll = enrollments.order_by("-enrolled_on").first()
                cache.set(
                    f"current_enroll_{player.id}", current_enroll, 300
                )  # Cache enrollments for 3 minutes

            current_draft = (
                Draft.objects.filter(
                    ~Q(finished=True), enrollments__in=[current_enroll]
                )
                .order_by("phase__phase_idx")
                .first()
            )
            cache.set(
                f"draft_{user.id}", current_draft, 120
            )  # Cache draft object for 2 minutes

        images = Image.objects.filter(
            user=user, draft_idx=current_draft.id, checkin=False
        )
        return render(
            request,
            "tournaments/my_pool_checkout.html",
            {"images": images},
        )
