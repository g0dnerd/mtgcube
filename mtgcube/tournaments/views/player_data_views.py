from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
import json
from django.utils.translation import gettext as _
from django.urls import reverse_lazy

from ..forms import ImageForm
from .. import queries as queries
from ..models import Image

from django.views import View


PRONOUN_CHOICES = {
    "x": _("(they/them)"),
    "m": _("(he/him)"),
    "f": _("(she/her)"),
    "n": _("(neither/don't want to say)"),
}


class PlayerBasicInfoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user

        player = queries.player(user)
        tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
        current_enroll = queries.enrollment_from_tournament(tournament, player)

        draft = queries.get_draft(id=kwargs['draft_id'])

        player_json = {
            "name": user.name if user.name else user.username,
            "signup_status": current_enroll.registration_finished,
            "draft_seated": draft.seated,
            "checked_in": current_enroll.checked_in,
            "checked_out": current_enroll.checked_out,
        }

        return JsonResponse(player_json)


class PlayerDraftInfoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Get user info from cache
        user = request.user
        player = queries.player(user)
        tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
        try:
            current_enroll = queries.enrollment_from_tournament(tournament, player)
            current_draft = queries.current_draft(current_enroll, user.id)
        except ValueError:
            return JsonResponse({"error": True})
        try:
            current_round = queries.current_round(current_draft, force_update=True)
            current_round_idx = current_round.round_idx if current_round else 0
        except ValueError:
            current_round = None
            current_round_idx = None

        draft_json = {
            "id": current_draft.id,
            "current_round": str(current_round_idx),
            "cube_name": current_draft.cube.name,
            "cube_url": current_draft.cube.url,
            "cube_slug": current_draft.cube.slug,
            "seated": current_draft.seated,
            "finished": current_draft.finished,
        }

        return JsonResponse(draft_json)

class PlayerMatchInfoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            player = queries.player(user)
            tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
            current_enroll = queries.enrollment_from_tournament(tournament, player)
        except ValueError as e:
            return JsonResponse({"error": _(str(e))}, status=404)
        
        current_draft = queries.current_draft(current_enroll, user.id)
        current_round = queries.current_round(current_draft, force_update=True)

        if not current_round:
            return JsonResponse({"error": "Not started."}, status=200,)

        if not current_enroll.checked_in:
            return JsonResponse({"error": "No checkin."}, status=200,)

        if current_enroll.bye_this_round:
            return JsonResponse({"match": {"bye": True}}, status=200)

        current_match = queries.current_match(
            current_enroll, current_round, user.id, force_update=True
        )
        if not current_match:
            return JsonResponse({"error": "No match yet."})

        opponent = current_match.player2
        if current_match.player2 == current_enroll:
            opponent = current_match.player1

        opp_pronouns = _(PRONOUN_CHOICES[opponent.player.user.pronouns])

        match_json = {
            "id": current_match.id,
            "table": current_match.table,
            "player1": current_match.player1.player.user.name,
            "player2": current_match.player2.player.user.name,
            "current_round": current_round.round_idx,
            "opponent": opponent.player.user.name,
            "opp_pronouns": opp_pronouns,
        }

        return JsonResponse(match_json)


class PlayerFullMatchInfoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            player = queries.player(user)
            tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
            current_enroll = queries.enrollment_from_tournament(tournament, player)
            if current_enroll.bye_this_round:
                return JsonResponse({"match": {"bye": True}}, status=200)
            current_match = queries.match_from_id(kwargs['match_id'], force_update=True)
        except ValueError as e:
            return JsonResponse({"error": _(str(e))}, status=404)

        if not current_enroll.checked_in:
            return JsonResponse({"error": "No checkin."}, status=200,)

        player_role = 1
        opponent = current_match.player2
        if current_match.player2 == current_enroll:
            player_role = 2
            opponent = current_match.player1

        opp_pronouns = _(PRONOUN_CHOICES[opponent.player.user.pronouns])

        # Format the game result to the POV of the current user
        winner = False
        if current_match.result_reported_by:
            if current_match.player2_wins > current_match.player1_wins:
                winner = current_match.player2.player.user.name
                current_match.result = (
                    f"{current_match.player2_wins}-{current_match.player1_wins}"
                )
                current_match.save()
            elif current_match.player1_wins > current_match.player2_wins:
                winner = current_match.player1.player.user.name

        match_json = {
            "name": current_enroll.player.user.name,
            "id": current_match.id,
            "table": current_match.table,
            "player1": current_match.player1.player.user.name,
            "player2": current_match.player2.player.user.name,
            "current_round": current_match.round.round_idx,
            "result": current_match.game_result_formatted(),
            "result_confirmed": current_match.result_confirmed,
            "reported_by": current_match.result_reported_by,
            "opponent": opponent.player.user.name,
            "opp_pronouns": opp_pronouns,
            "player_role": player_role,
            "winner": winner,
        }

        return JsonResponse(match_json)


class PlayerOtherPairingsInfoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            player = queries.player(user)
            tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
            current_enroll = queries.enrollment_from_tournament(tournament, player)
            draft_id = kwargs.get("draft_id")
            current_draft = queries.get_draft(id=draft_id)
            current_round = queries.current_round(current_draft, force_update=True)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=404)

        if not current_round or not current_round.paired:
            return JsonResponse(
                {"error": "No pairings yet."}, status=200
            )

        try:
            non_player_games = queries.non_player_games(
                current_enroll, current_round, user.id
            )
        except ValueError:
            return JsonResponse({"error": "No pairings yet."}, status=200)

        if not current_enroll.checked_in:
            return JsonResponse({"error": "No check-in."}, status=200,)

        other_pairings = [
            {
                "id": game.id,
                "table": game.table,
                "player1": game.player1.player.user.name,
                "player2": game.player2.player.user.name,
                "result": game.result,
                "player1_wins": game.player1_wins,
                "player2_wins": game.player2_wins,
            }
            for game in non_player_games
        ]

        bye_this_round = queries.bye_this_round(current_draft)

        return JsonResponse({"other_pairings": other_pairings, "bye": bye_this_round})


class ReportResultView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        game_id = data.get("game_id")
        player1_wins = data.get("player1_wins")
        player2_wins = data.get("player2_wins")

        if int(player1_wins) + int(player2_wins) > 3:
            messages.error(request, "Error: Please enter a valid game result.")
            return JsonResponse({"error": "Invalid game result"}, status=403)

        player = queries.player(request.user)
        match = queries.match_from_id(game_id)

        if match:
            match.player1_wins = player1_wins
            match.player2_wins = player2_wins
            match.result = f"{player1_wins}-{player2_wins}"
            match.result_reported_by = player.user.name
            match.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"error": "Game not found"}, status=404)


class AnnouncementView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            player = queries.player(user)
            tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
            current_enroll = queries.enrollment_from_tournament(tournament, player)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=404)

        tournament = current_enroll.tournament
        if tournament.announcement:
            return JsonResponse({"announcement": tournament.announcement})
        return JsonResponse({"error": "no announcement"})


class TimetableView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            player = queries.player(user)
            tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
            current_enroll = queries.enrollment_from_tournament(tournament, player)
            upcoming_drafts = queries.timetable(tournament, current_enroll, user.id)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=404)

        timetable = [
            {
                "id": d.id,
                "cube": d.cube.name,
                "cube_url": d.cube.url,
                "cube_slug": d.cube.slug,
                "round_number": d.round_number,
                "first_round": (d.phase.phase_idx - 1) * d.round_number + 1,
                "last_round": d.round_number * d.phase.phase_idx,
                "phase_idx": d.phase.phase_idx,
            }
            for d in upcoming_drafts
        ]

        return JsonResponse({"timetable": timetable})


class CheckinView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            try:
                player = queries.player(user)
                tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
                current_enroll = queries.enrollment_from_tournament(tournament, player)
                current_draft = queries.current_draft(
                    current_enroll, user.id, force_update=True
                )
            except ValueError as e:
                return JsonResponse({"error": str(e)}, status=404)

            draft_id = current_draft.id

            form.instance.user = request.user
            form.instance.draft_idx = draft_id
            form.save()

            current_enroll.checked_in = True
            current_enroll.save()

            return redirect(reverse_lazy("tournaments:my_pool_checkin", kwargs=kwargs))

    def get(self, request, *args, **kwargs):
        form = ImageForm()
        return render(
            request,
            "tournaments/checkin.html",
            {"form": form},
        )


class CheckoutView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user

            try:
                player = queries.player(user)
                tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
                current_enroll = queries.enrollment_from_tournament(tournament, player)
                current_draft = queries.current_draft(current_enroll, user.id)
            except ValueError as e:
                return JsonResponse({"error": str(e)}, status=404)

            form.instance.user = request.user
            form.instance.draft_idx = current_draft.id
            form.instance.checkin = False
            form.save()

            current_enroll.checked_out = True
            current_enroll.save()
            return redirect(reverse_lazy("tournaments:my_pool_checkout", kwargs=kwargs))

    def get(self, request, *args, **kwargs):
        form = ImageForm()
        return render(
            request,
            "tournaments/checkout.html",
            {"form": form},
        )


class DeleteImageCheckinView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        image_id = kwargs.get("image_id")
        image = get_object_or_404(Image, id=image_id, user=request.user)
        default_storage.delete(image.image.name)
        image.delete()

        user = request.user
        player = queries.player(user)
        tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
        current_enroll = queries.enrollment_from_tournament(tournament, player)
        current_draft = queries.current_draft(current_enroll, user.id)
        if not current_draft:
            return JsonResponse({"error": True}, status=404)

        images = queries.images(user, current_draft, checkin=True)
        if not images:
            current_enroll.checked_in = False
            current_enroll.save()

        return redirect(reverse_lazy("tournaments:my_pool_checkin", kwargs={"slug": kwargs['slug']}))


class DeleteImageCheckoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        image_id = kwargs.get("image_id")
        image = get_object_or_404(Image, id=image_id, user=request.user)
        default_storage.delete(image.image.name)
        image.delete()

        user = request.user
        player = queries.player(user)
        tournament = queries.get_tournament(tournament_slug=kwargs['slug'])
        current_enroll = queries.enrollment_from_tournament(tournament, player)
        current_draft = queries.current_draft(current_enroll, user.id)
        if not current_draft:
            return JsonResponse({"error": True}, status=404)

        images = queries.images(user, current_draft, checkin=False)
        if not images:
            current_enroll.checked_out = False
            current_enroll.save()
        
        return redirect(reverse_lazy("tournaments:my_pool_checkout", kwargs={"slug": kwargs['slug']}))
