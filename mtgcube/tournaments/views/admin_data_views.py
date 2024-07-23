import json

from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Prefetch
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page

from ..models import Tournament, Draft, Round, Game, Enrollment
from .. import services as services


class AdminDraftsView(LoginRequiredMixin, View):
    @method_decorator(cache_page(60))  # Cache the entire view for 1 minute
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse({"error": "Missing authentication level"})

        # Get the latest tournament
        tournament = cache.get("latest_tournament")
        if not tournament:
            tournament = Tournament.objects.order_by("-start_datetime").first()
            cache.set("latest_tournament", tournament, 60)  # Cache for 1 minute

        # Fetch drafts with optimized queries
        drafts = (
            Draft.objects.filter(phase__tournament=tournament, started=True)
            .order_by("-phase__phase_idx")
            .select_related("cube")
            .prefetch_related(
                Prefetch(
                    "round_set",
                    queryset=Round.objects.order_by("-round_idx").prefetch_related(
                        Prefetch(
                            "game_set",
                            queryset=Game.objects.select_related(
                                "player1__player__user", "player2__player__user"
                            ),
                        )
                    ),
                ),
                Prefetch("enrollments__player__user"),
            )
        )


        # Fetch event standings
        event_standings = cache.get(f"event_standings_{tournament.id}")
        if not event_standings:
            event_standings = services.event_standings(tournament)
            cache.set(
                f"event_standings_{tournament.id}", event_standings, 60
            )  # Cache for 1 minute

        event_standings_out = [
            {
                "name": enrollment.player.user.name,
                "score": enrollment.score,
                "omw": enrollment.omw,
                "pgw": enrollment.pgw,
                "ogw": enrollment.ogw,
            }
            for enrollment in event_standings
        ]

        drafts_out = []
        for draft in drafts:
            player_names = [
                enrollment.player.user.name for enrollment in draft.enrollments.all()
            ]

            drafts_out.append(
                {
                    "id": draft.id,
                    "cube_name": draft.cube.name,
                    "cube_url": draft.cube.url,
                    "players": player_names,
                }
            )

        return JsonResponse(
            {"drafts": drafts_out, "event_standings": event_standings_out}
        )


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
                "error": f"Not returning seatings because draft is already in round {current_round.round_idx}"
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


class PairRoundView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(
                {"error": "Insufficient authentication level"}, status=403
            )

        data = json.loads(request.body)
        draft_id = data.get("draft_id")
        draft = get_object_or_404(Draft, pk=draft_id)
        rd = Round.objects.filter(draft=draft).order_by("-round_idx").first()

        services.pair_round(rd)

        return JsonResponse({"success": True}, status=200)


class SeatDraftView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(
                {"error": "Insufficient authentication level"}, status=403
            )

        data = json.loads(request.body)
        draft_id = data.get("draft_id")

        draft = get_object_or_404(Draft, pk=draft_id)
        if not draft.seated:
            services.seatings(draft)
        return JsonResponse({"success": True}, status=200)


class ClearHistoryView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(
                {"error": "Insufficient authentication level"}, status=403
            )

        data = json.loads(request.body)
        draft_id = data.get("draft_id")

        draft = get_object_or_404(Draft, pk=draft_id)
        services.clear_histories(draft)
        return JsonResponse({"success": True}, status=200)


class FinishRoundView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(
                {"error": "Insufficient authentication level"}, status=403
            )

        data = json.loads(request.body)
        draft_id = data.get("draft_id")
        draft = get_object_or_404(Draft, pk=draft_id)
        current_rd = Round.objects.filter(draft=draft).order_by("-round_idx").first()

        services.update_tiebreakers(draft)
        current_rd.finished = True
        current_rd.save()

        if current_rd.round_idx == draft.round_number:
            draft.finished = True
            draft.save()
            services.reset_draft_scores(draft)
        else:
            services.finish_round(current_rd)
            new_rd = Round(
                draft = draft,
                round_idx = current_rd.round_idx + 1
            )
            new_rd.save()

        return JsonResponse({"success": True}, status=200)

class StartRoundView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(
                {"error": "Insufficient authentication level"}, status=403
            )

        data = json.loads(request.body)
        draft_id = data.get("draft_id")

        draft = get_object_or_404(Draft, pk=draft_id)
        round = Round.objects.filter(draft=draft).order_by("-round_idx").first()
        round.started = True
        round.save()
        return JsonResponse({"success": True}, status=200)

class SyncRoundView(LoginRequiredMixin, View):
     def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(
                {"error": "Insufficient authentication level"}, status=403
            )

        data = json.loads(request.body)
        draft_id = data.get("draft_id")
        draft = get_object_or_404(Draft, pk=draft_id)
        
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

        matches = current_round.game_set.select_related(
            "player1__player__user", "player2__player__user"
        )

        services.sync_round(matches)
        return JsonResponse({"success": True})