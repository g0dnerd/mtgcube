from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from .. import queries


class AdminDraftInfoEmbedView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse({"error": "Missing authentication level"}, status=403)

        draft = queries.get_draft(slug=kwargs["draft_slug"])

        players = [
            enrollment.player.user.name for enrollment in draft.enrollments.all()
        ]

        current_round = queries.current_round(draft, force_update=True)
        matches = None
        if current_round:
            matches = queries.matches_from_draft(draft, current_round)

        # Check if there are matches in progress
        in_progress = False
        if matches:
            for match in matches:
                if not match.result_confirmed:
                    in_progress = True
                    break

        draft_finished = False

        if not current_round:
            paired = False
            rd_finished = False
            rd_idx = 0
        else:
            rd_finished = current_round.finished
            if rd_finished and current_round.round_idx == draft.round_number:
                draft_finished = True
            paired = current_round.paired
            rd_idx = current_round.round_idx

        return JsonResponse(
            {
                "cube": draft.cube.name,
                "cube_url": draft.cube.url,
                "players": players,
                "seated": draft.seated,
                "started": draft.started,
                "finished": rd_finished,
                "paired": paired,
                "in_progress": in_progress,
                "draft_round": rd_idx,
                "event_round": draft.phase.tournament.current_round,
                "draft_finished": draft_finished,
            }
        )


class AdminMatchInfoEmbedView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse({"error": "Missing authentication level"}, status=403)

        match_id = self.kwargs["match_id"]

        match = queries.get_match(match_id)

        return JsonResponse(
            {
                "table": match.table,
                "player1": match.player1.player.user.name,
                "player2": match.player2.player.user.name,
                "player1_wins": match.player1_wins,
                "player2_wins": match.player2_wins,
                "result": match.game_result_formatted(),
                "result_confirmed": match.result_confirmed,
                "reported_by": match.result_reported_by,
            }
        )