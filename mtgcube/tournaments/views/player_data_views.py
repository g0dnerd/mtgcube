from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
import json

from ..forms import ImageForm
from .. import services
from ..models import (
    Draft,
    Enrollment,
    Game,
    Player,
    Round,
    Tournament,
    Image,
)

from django.views import View


class PlayerDraftInfoView(LoginRequiredMixin, View):
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
                return JsonResponse(
                    {"error": "No player found for current user"}, status=404
                )
        
        enrollments = cache.get(f"enrollments_{player.id}")
        if not enrollments:
            enrollments = Enrollment.objects.filter(player=player).select_related(
                "tournament"
            )
            cache.set(
                f"enrollments_{user.id}", enrollments, 300
            )  # Cache draft object for 5 minutes
    
        current_enroll = cache.get(f"current_enroll_{player.id}")
        if not current_enroll:
            current_enroll = enrollments.order_by("-enrolled_on").first()
            cache.set(
                f"current_enroll_{player.id}", current_enroll, 300
            )  # Cache enrollments for 5 minute

        current_draft = cache.get(f"draft_{player.id}")
        if not current_draft:
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
            return JsonResponse({"error": "No active draft for current user"})

        current_round = (
            Round.objects.filter(draft=current_draft).order_by("-round_idx").first()
        )

        cridx = current_round.round_idx if current_round else 0

        draft_json = {
            "id": current_draft.id,
            "current_round": str(cridx),
            "cube_name": current_draft.cube.name,
            "cube_url": current_draft.cube.url,
            "finished": current_draft.finished,
        }

        return JsonResponse({"draft": draft_json})


class PlayerMatchInfoView(LoginRequiredMixin, View):
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
                return JsonResponse(
                    {"error": "No player found for current user"}, status=404
                )
            
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

        if current_enroll.bye_this_round:
            return JsonResponse({"match": {"bye": True}}, status=200)

        current_draft = cache.get(f"draft_{player.id}")
        if not current_draft:
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

        try:
            current_round = (
                Round.objects.filter(draft=current_draft).order_by("-round_idx").first()
            )
        except Round.DoesNotExist:
            return JsonResponse({"error": "Round has not yet been paired."}, status=200)

        try:
            current_match = Game.objects.get(
                Q(player1=current_enroll) | Q(player2=current_enroll),
                round=current_round,
            )
        except Game.DoesNotExist:
            return JsonResponse({"error": "Round has not yet been paired."}, status=200)

        player_role = 1
        if current_match.player2 == current_enroll:
            player_role = 2
            opponent = current_match.player1
        else:
            opponent = current_match.player2
            player_role = 0

        pronoun_choices = {"x": "they/them", "m": "he/him", "f": "she/her"}
        match_json = {
            "id": current_match.id,
            "table": current_match.table,
            "player1": current_match.player1.player.user.name,
            "player2": current_match.player2.player.user.name,
            "current_round": current_round.round_idx,
            "result": current_match.game_result_formatted(),
            "result_confirmed": current_match.result_confirmed,
            "reported_by": current_match.result_reported_by,
            "opponent": opponent.player.user.name,
            "opp_pronouns": pronoun_choices[opponent.player.user.pronouns],
            "player_role": player_role,
        }
        player_json = {
            "name": current_enroll.player.user.name,
        }

        return JsonResponse({"match": match_json, "player": player_json})


class PlayerBasicInfoView(LoginRequiredMixin, View):
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
                return JsonResponse(
                    {"error": "No player found for current user"}, status=404
                )

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

        player_json = {
            "name": player.user.name if player.user.name else player.user.username,
            "tournament_name": str(current_enroll.tournament),
            "score": current_enroll.score,
            "signup_status": current_enroll.registration_finished,
            "checked_in": current_enroll.checked_in,
            "checked_out": current_enroll.checked_out,
        }

        return JsonResponse({"player": player_json})


class PlayerOtherPairingsInfoView(LoginRequiredMixin, View):
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
                return JsonResponse(
                    {"error": "No player found for current user"}, status=404
                )
            
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

        current_draft = cache.get(f"draft_{player.id}")
        if not current_draft:
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

        current_round = (
            Round.objects.filter(draft=current_draft).order_by("-round_idx").first()
        )

        if not current_round or not current_round.paired:
            return JsonResponse({"error": "Round has not yet been paired."}, status=200)

        try:
            non_player_games = Game.objects.filter(
                ~(Q(player1=current_enroll) | Q(player2=current_enroll)),
                round=current_round,
            ).order_by("table")
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

            try:
                bye_this_round = current_draft.enrollments.get(bye_this_round=True)
                if bye_this_round == current_enroll:
                    bye_this_round = False
                else:
                    bye_this_round = bye_this_round.player.user.name
            except Enrollment.DoesNotExist:
                bye_this_round = False

        except Game.DoesNotExist:
            return JsonResponse({"error": "No pairings yet."}, status=200)

        return JsonResponse({"other_pairings": other_pairings, "bye": bye_this_round})


class PlayerSeatingsView(LoginRequiredMixin, View):
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
                return JsonResponse(
                    {"error": "No player found for current user"}, status=404
                )

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

        current_draft = cache.get(f"draft_{player.id}")
        if not current_draft:
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

        if not current_draft.seated:
            return JsonResponse({"error": "Draft has not been seated yet"}, status=200)

        current_round = (
            Round.objects.filter(draft=current_draft).order_by("-round_idx").first()
        )

        # Get seatings
        if current_round.started or current_round.paired:
            seatings_out = {
                "error": f"Not returning seatings because draft is already in round {current_round.round_idx}"
            }
        else:
            sorted_players = list(current_draft.enrollments.all().order_by("seat"))
            seatings_out = [
                {
                    "seat": player.seat,
                    "id": player.id,
                    "name": player.player.user.name,
                }
                for player in sorted_players
            ]

        return JsonResponse({"seatings": seatings_out})


class PlayerStandingsView(LoginRequiredMixin, View):
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
                return JsonResponse(
                    {"error": "No player found for current user"}, status=404
                )
        
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

        current_draft = cache.get(f"draft_{player.id}")
        if not current_draft:
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

        current_round = (
            Round.objects.filter(draft=current_draft).order_by("-round_idx").first()
        )

        # Get standings
        if  not current_round or current_round.round_idx == 1 and not current_round.finished:
            return JsonResponse({"error": "Draft has no standings yet."}, status=200)
        else:
            sorted_players = services.draft_standings(current_draft, update=False)
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

        return JsonResponse({"standings": standings_out, "current_round": current_round.round_idx})


class ReportResultView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        game_id = data.get("game_id")
        player1_wins = data.get("player1_wins")
        player2_wins = data.get("player2_wins")

        game = get_object_or_404(Game, pk=game_id)
        user = request.user
        player = Player.objects.get(user=user)

        if game:
            game.player1_wins = player1_wins
            game.player2_wins = player2_wins
            game.result = f"{player1_wins}-{player2_wins}"
            game.result_reported_by = player.user.name
            game.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"error": "Game not found"}, status=404)


class ConfirmResultView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        game_id = data.get("game_id")

        game = get_object_or_404(Game, pk=game_id)

        if game:
            game.result_confirmed = True
            services.update_result(game, game.player1_wins, game.player2_wins)
            game.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"error": "Game not found"}, status=404)


class AnnouncementView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        tournament = cache.get('latest_event')
        if not tournament:
            user = request.user
            player = cache.get(f"player_{user.id}")
            if not player:
                try:
                    player = Player.objects.get(user=user)
                    cache.set(
                        f"player_{user.id}", player, 300
                    )  # Cache player object for 5 minutes
                except Player.DoesNotExist:
                    return JsonResponse(
                        {"error": "No player found for current user"}, status=404
                    )

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
            tournament = current_enroll.tournament
            cache.set(
                "current_event", tournament, 300
            )

        if tournament.announcement:
            return JsonResponse({"announcement": tournament.announcement})
        return JsonResponse({"error": "no announcement"})


class UpcomingDraftView(LoginRequiredMixin, View):
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
                return JsonResponse(
                    {"error": "No player found for current user"}, status=404
                )

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

        try:
            drafts = Draft.objects.filter(
                started=False, enrollments__in=[current_enroll]
            ).order_by("-phase")
            next_draft = drafts[0]
        except IndexError:
            return JsonResponse({"error": "No upcoming draft found."}, status=200)

        return JsonResponse(
            {
                "upcoming_draft": {
                    "id": next_draft.id,
                    "cube": next_draft.cube.name,
                    "cube_url": next_draft.cube.url,
                    "round_number": next_draft.round_number,
                }
            }
        )


@login_required
def round_status(request, tournament_id, draft_id):
    user = request.user
    if not user.is_superuser:
        return redirect("tournaments:tournament", tournament_id)

    draft = get_object_or_404(Draft, pk=draft_id)
    round = Round.objects.filter(draft=draft).order_by("-round_idx").first()
    games = Game.objects.filter(round=round)
    ongoing = False
    for game in games:
        if not game.result_confirmed:
            ongoing = True
            break

    return JsonResponse({"ongoing": ongoing, "started": round.started})


@login_required
def checkin(request):
    if request.method == "POST":
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            tournament_id, draft_id = services.tournament_draft_ids(request.user)
            form.instance.user = request.user
            form.instance.draft_idx = draft_id
            form.save()
            tournament = get_object_or_404(Tournament, pk=tournament_id)
            player = Player.objects.get(user=request.user)
            enrollment = Enrollment.objects.get(tournament=tournament, player=player)
            enrollment.checked_in = True
            enrollment.save()
            return redirect("tournaments:my_pool_checkin")
    else:
        form = ImageForm()
    return render(
        request,
        "tournaments/checkin.html",
        {"form": form},
    )


@login_required
def checkout(request):
    if request.method == "POST":
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            tournament_id, draft_id = services.tournament_draft_ids(request.user)
            form.instance.user = request.user
            form.instance.draft_idx = draft_id
            form.instance.checkin = False
            form.save()
            tournament = get_object_or_404(Tournament, pk=tournament_id)
            player = Player.objects.get(user=request.user)
            enrollment = Enrollment.objects.get(tournament=tournament, player=player)
            enrollment.checked_out = True
            enrollment.save()
            return redirect("tournaments:my_pool_checkout")
    else:
        form = ImageForm()
    return render(
        request,
        "tournaments/checkin.html",
        {"form": form},
    )


@login_required
def delete_image_checkin(request, image_id):
    image = get_object_or_404(Image, id=image_id, user=request.user)
    default_storage.delete(image.image.name)
    image.delete()
    return redirect("tournaments:my_pool_checkin")


@login_required
def delete_image_checkout(request, image_id):
    image = get_object_or_404(Image, id=image_id, user=request.user)
    default_storage.delete(image.image.name)
    image.delete()
    return redirect("tournaments:my_pool_checkout")


@login_required
def replace_image_checkin(request, image_id):
    image = get_object_or_404(Image, id=image_id, user=request.user)
    if request.method == "POST":
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            _, draft_id = services.tournament_draft_ids(request.user)
            # Delete the old image
            default_storage.delete(image.image.name)
            image.image.delete()
            # Update with new image
            image.image = request.FILES["image"]
            image.draft_idx = draft_id
            image.save()
            return redirect("tournaments:my_pool_checkin")
    else:
        form = ImageForm()
    return render(
        request,
        "tournaments/replace_image.html",
        {
            "form": form,
            "image": image,
        },
    )


@login_required
def replace_image_checkout(request, image_id):
    image = get_object_or_404(Image, id=image_id, user=request.user)
    if request.method == "POST":
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            _, draft_id = services.tournament_draft_ids(request.user)
            # Delete the old image
            default_storage.delete(image.image.name)
            image.image.delete()
            # Update with new image
            image.image = request.FILES["image"]
            image.draft_idx = draft_id
            image.checkin = False
            image.save()
            return redirect("tournaments:my_pool_checkout")
    else:
        form = ImageForm()
    return render(
        request,
        "tournaments/replace_image.html",
        {
            "form": form,
            "image": image,
        },
    )
