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
        matches = queries.matches_from_draft(draft, force_update=True)

        # Check if there are matches in progress
        in_progress = False
        if matches:
            for match in matches:
                if not match.result_confirmed:
                    in_progress = True
                    break

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
                "finished": draft.finished,
                "paired": paired,
                "in_progress": in_progress,
            }
        )


class AdminMatchInfoEmbedView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse({"error": "Missing authentication level"}, status=403)

        match_id = self.kwargs["match_id"]

        match = queries.match_from_id(match_id, force_update=True)

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