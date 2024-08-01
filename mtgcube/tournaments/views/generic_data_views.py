from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from .. import queries


class SeatingsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        draft = queries.get_draft(id=kwargs['draft_id'], force_update=True)

        if not draft.seated:
            return JsonResponse({"error": "No seatings yet."}, status=200)

        current_round = queries.current_round(draft)
    
        # Get seatings
        if current_round:
            if current_round.started or current_round.paired or current_round.round_idx > 1:
                return JsonResponse({"error": "No seatings anymore."})

        sorted_players = list(draft.enrollments.all().order_by("seat"))
        seatings_out = [
            {
                "seat": player.seat,
                "id": player.id,
                "name": player.player.user.name,
            }
            for player in sorted_players
        ]
        return JsonResponse({"seatings": seatings_out})


class PlayerListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        draft = queries.get_draft(id=kwargs['draft_id'])

        players = [
            enrollment.player.user.name for enrollment in draft.enrollments.all()
        ]

        return JsonResponse({"players": players})


class DraftStandingsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        draft = queries.get_draft(id=kwargs['draft_id'])

        # Get standings
        
        sorted_players = queries.draft_standings(draft)
        if not sorted_players:
            return JsonResponse({"error": "No draft standings yet."}, status=200)
        
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

        current_round = queries.current_round(draft, force_update=True)
        rd_idx = min(draft.phase.tournament.current_round, current_round.round_idx)

        return JsonResponse(
            {"standings": standings_out, "current_round": rd_idx}
        )


class EventStandingsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        tournament = queries.get_tournament(tournament_slug=kwargs['slug'], force_update=True)

        sorted_players = queries.tournament_standings(tournament)
        if not sorted_players:
            return JsonResponse({"error": "No event standings yet."})

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

        return JsonResponse({"standings": standings_out, "current_round": tournament.current_round - 1})
