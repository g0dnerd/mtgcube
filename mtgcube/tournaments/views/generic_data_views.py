from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from .. import queries


class SeatingsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        draft = queries.get_draft(slug=kwargs['draft_slug'])

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
        draft = queries.get_draft(slug=kwargs['draft_slug'])

        players = [
            enrollment.player.user.name for enrollment in draft.enrollments.filter(dropped=False)
        ]

        return JsonResponse({"players": players})


class DraftStandingsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        draft = queries.get_draft(slug=kwargs['draft_slug'])

        # Get standings
        standings = queries.draft_standings(draft)
        if not standings:
            return JsonResponse({"error": "No draft standings yet."}, status=200)
        
        current_round = queries.current_round(draft, force_update=True)
        
        if not current_round.finished:
            rd_idx = current_round.round_idx - 1
        else:
            rd_idx = current_round.round_idx

        return JsonResponse(
            {"standings": standings, "current_round": rd_idx}
        )


class EventStandingsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        tournament = queries.get_tournament(slug=kwargs['slug'], force_update=True)

        standings = queries.tournament_standings(tournament)
        if not standings:
            return JsonResponse({"error": "No event standings yet."})

        return JsonResponse({"standings": standings, "current_round": tournament.current_round - 1})
