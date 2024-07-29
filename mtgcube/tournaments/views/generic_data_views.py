from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.utils.translation import gettext as _

from .. import services, queries


class SeatingsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        draft = queries.draft_from_id(kwargs['draft_id'])

        if not draft.seated:
            return JsonResponse({"error": "Draft has not been seated yet."}, status=200)

        current_round = queries.current_round(draft)
    
        # Get seatings
        if current_round.started or current_round.paired or current_round.round_idx > 1:
            error_message = _("Round %(round)s has already started.") % {"round": current_round.round_idx}
            return JsonResponse({"error": error_message})

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
        draft = queries.draft_from_id(kwargs['draft_id'])

        players = [
            enrollment.player.user.name for enrollment in draft.enrollments.all()
        ]

        return JsonResponse({"players": players})


class DraftStandingsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        draft = queries.draft_from_id(kwargs['draft_id'])

        try:
            current_round = queries.current_round(draft)
        except ValueError:
            current_round = None

        # Get standings
        if (
            not current_round
            or current_round.round_idx == 1
            and not current_round.finished
        ):
            return JsonResponse({"error": "Draft has no standings yet."}, status=200)
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

        return JsonResponse(
            {"standings": standings_out, "current_round": current_round.round_idx - 1}
        )


class EventStandingsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        tournament = queries.get_tournament(tournament_slug=kwargs['slug'])

        if tournament.current_round <= 1:
            return JsonResponse({"error": _("Standings will show up here after the first round has finished.")})

        sorted_players = services.event_standings(tournament)

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
