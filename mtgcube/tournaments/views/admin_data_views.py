from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.http import JsonResponse
from django.views import View
from django.utils.translation import gettext as _

from ..models import Draft, Round, Enrollment, Game
from .. import services as services


class AdminDraftInfoEmbedView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse({"error": "Missing authentication level"})

        draft_id = self.kwargs["draft_id"]
        draft = get_object_or_404(
            Draft.objects.select_related("cube").prefetch_related(
                Prefetch("enrollments__player__user", to_attr="enrolled_players"),
            ),
            pk=draft_id,
        )

        players = [
            enrollment.player.user.name for enrollment in draft.enrollments.all()
        ]

        current_round = (
            Round.objects.filter(draft=draft)
            .order_by("-round_idx")
            .select_related("draft")
            .prefetch_related(
                Prefetch("game_set__player1__player__user"),
                Prefetch("game_set__player2__player__user"),
            )
            .first()
        )

        if not current_round:
            paired = False
        else:
            paired = current_round.paired

        return JsonResponse(
            {
                "cube": draft.cube.name,
                "cube_url": draft.cube.url,
                "players": players,
                "seated": draft.seated,
                "started": draft.started,
                "paired": paired,
            }
        )


class AdminMatchInfoEmbedView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse({"error": "Missing authentication level"})

        match_id = self.kwargs["match_id"]

        match = get_object_or_404(Game, pk=match_id)
        
        return JsonResponse({
            "table": match.table,
            "player1": match.player1.player.user.name,
            "player2": match.player2.player.user.name,
            "player1_wins": match.player1_wins,
            "player2_wins": match.player2_wins,
            "result": match.game_result_formatted(),
            "result_confirmed": match.result_confirmed,
            "reported_by": match.result_reported_by,
        })




class AdminDraftInfoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse({"error": "Missing authentication level"})

        draft_id = self.kwargs["draft_id"]
        draft = get_object_or_404(
            Draft.objects.select_related("cube").prefetch_related(
                Prefetch("enrollments__player__user", to_attr="enrolled_players"),
            ),
            pk=draft_id,
        )

        players = [
            enrollment.player.user.name for enrollment in draft.enrollments.all()
        ]

        current_round = (
            Round.objects.filter(draft=draft)
            .order_by("-round_idx")
            .select_related("draft")
            .prefetch_related(
                Prefetch("game_set__player1__player__user"),
                Prefetch("game_set__player2__player__user"),
            )
            .first()
        )

        if not current_round:
            info = {
                "started": draft.started,
                "cube": draft.cube.name,
                "cube_url": draft.cube.url,
                "finished": False,
                "in_progress": False,
                "seated": False,
                "round_paired": False,
                "round_finished": False,
                "standings": False,
            }
            return JsonResponse(
                {
                    "info": info,
                    "players": players,
                    "standings": {"error": "No standings yet"},
                    "seatings": {"error": "No seatings yet"},
                    "matches": {"error": "No matches yet"},
                }
            )

        if current_round.round_idx == 1 and not current_round.finished:
            standings_out = {"error": "Draft has no standings yet."}
        else:
            sorted_players = services.draft_standings(draft, update=False)
            standings_out = [
                {
                    "name": enrollment.player.user.name,
                    "score": enrollment.draft_score,
                    "omw": enrollment.draft_omw,
                    "pgw": enrollment.draft_pgw,
                    "ogw": enrollment.draft_ogw,
                }
                for enrollment in sorted_players
            ]

        if current_round.started or current_round.paired or current_round.round_idx > 1:
            seatings_out = {
                "error": f"{_('Round')} {current_round.round_idx} {_('has already started')}."
            }
        else:
            sorted_players = draft.enrollments.all().order_by("seat")
            seatings_out = [
                {
                    "seat": player.seat,
                    "id": player.id,
                    "name": player.player.user.name,
                }
                for player in sorted_players
            ]

        ongoing = any(
            game.game_result_formatted() == "Pending"
            for game in current_round.game_set.all()
        )
        standings_ready = current_round.round_idx == 1 and not current_round.finished

        info = {
            "started": draft.started,
            "cube": draft.cube.name,
            "cube_url": draft.cube.url,
            "current_round": current_round.round_idx,
            "finished": draft.finished,
            "in_progress": ongoing,
            "seated": draft.seated,
            "round_paired": current_round.paired,
            "round_finished": current_round.finished,
            "standings": standings_ready,
        }

        matches = current_round.game_set.select_related(
            "player1__player__user", "player2__player__user"
        ).order_by("table")
        matches_out = [
            {
                "id": m.id,
                "table": m.table,
                "result": m.game_result_formatted(),
                "result_confirmed": m.result_confirmed,
                "player1": m.player1.player.user.name,
                "player2": m.player2.player.user.name,
                "player1_wins": m.player1_wins,
                "player2_wins": m.player2_wins,
                "reported_by": m.result_reported_by,
            }
            for m in matches
        ]

        try:
            bye_this_round = draft.enrollments.get(bye_this_round=True).player.user.name
        except Enrollment.DoesNotExist:
            bye_this_round = False

        return JsonResponse(
            {
                "info": info,
                "matches": matches_out,
                "standings": standings_out,
                "players": players,
                "seatings": seatings_out,
                "bye": bye_this_round,
            }
        )