import json
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views import generic
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Tournament, Enrollment, Player, Game, Draft, Phase, Round
from . import services as services

class IndexView(generic.ListView):
    template_name = "tournaments/index.html"
    context_object_name = "all_tournaments"

    def get_queryset(self):
        return Tournament.objects.all()


@login_required
def all_events(request):
    user = request.user
    events = Tournament.objects.all()
    try:
        player = Player.objects.get(user=user)
        available_enrollments = []
        for event in events:
            event_enrollments = Enrollment.objects.filter(tournament=event)
            is_player_enrolled = event_enrollments.filter(player=player)
            if not is_player_enrolled:
                available_enrollments.append(event)
    except Player.DoesNotExist:
        available_enrollments = events

    return render(
        request, "tournaments/all_events.html", {"available": available_enrollments}
    )


@login_required
def my_events(request):
    user = request.user
    if user.is_superuser:
        tournaments = Tournament.objects.all()
        return render(request, "tournaments/my_events.html", {"tournaments": tournaments})
    try:
        player = Player.objects.get(user=user)
    except Player.DoesNotExist:
        return render(request, "tournaments/my_events.html", {"tournaments": []})  # Handle the case where the user is not a player
    enrollments = Enrollment.objects.filter(player=player)
    tournaments = []
    for en in enrollments:
        tournaments.append(en.tournament)    
    return render(request, "tournaments/my_events.html", {"tournaments": tournaments})


@login_required
def tournament_view(request, tournament_id):
    user = request.user
    if user.is_superuser:
        return redirect("tournaments:tournament_admin_view", tournament_id)
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    player = Player.objects.get(user=user)
    try:
        enrollments = Enrollment.objects.filter(player=player)
        enrollment = enrollments.get(tournament=tournament)
    except Enrollment.DoesNotExist:
        return redirect("tournaments:my_events")
    phase = Phase.objects.filter(tournament=tournament).order_by("-phase_idx").first()
    draft = Draft.objects.get(phase=phase, enrollments__in=[enrollment])
    draft_json = {
            "id": draft.id,
            "phase": draft.phase.phase_idx,
            "cube": draft.cube.name,
            "cube_url": draft.cube.url,
        }
    context = {
        "tournament": tournament,
        "draft": draft_json,
    }
    if not user.is_superuser:
        return render(request, "tournaments/tournament.html", context)


@login_required
def tournament_admin_view(request, tournament_id):
    user = request.user
    if not user.is_superuser:
        return redirect("tournaments:tournament_view", tournament_id)
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    phase = Phase.objects.filter(tournament=tournament).order_by("-phase_idx").first()
    drafts = Draft.objects.filter(phase=phase)
    
    draft_games = {}
    rounds = {}
    for draft in drafts:
        round = Round.objects.filter(draft=draft).order_by("-round_idx").first()
        games = Game.objects.filter(round=round)
        draft_game = [
            {
                "id": game.id,
                "table": game.table,
                "player1": game.player1.player.user.name,
                "player2": game.player2.player.user.name,
                "result": game.game_result_formatted(),
            }
            for game in games
        ]
        draft_games[draft.id] = draft_game
        rounds[draft.id] = round
    context = {
        "tournament": tournament,
        "drafts": drafts,
        "rounds": rounds,
        "draft_games": draft_games,
    }
    return render(request, "tournaments/tournament_admin.html", context)


@login_required
def enroll_view(request, tournament_id):
    user = request.user
    try:
        player = Player.objects.get(user=user)
    except Player.DoesNotExist:
        Player.objects.create(user=user, name=user.name)
        player = Player.objects.get(user=user)
    tournament = get_object_or_404(Tournament, pk=tournament_id)

    # Catch duplicate enrollment attempts
    event_active_enrollments = Enrollment.objects.filter(
        tournament=tournament, player=player
    )
    if event_active_enrollments.exists():
        return redirect("tournaments:all_events")

    context = {
        "user": user,
        "tournament": tournament,
    }
    return render(request, "tournaments/enroll.html", context)


@login_required
def enroll_user_view(request, tournament_id):
    user = request.user
    player = Player.objects.get(user=user)
    tournament = get_object_or_404(Tournament, pk=tournament_id)

    Enrollment.objects.create(player=player, tournament=tournament)
    return redirect("tournaments:my_events")


@login_required
def pair_round_view(request, tournament_id, draft_id):
    user = request.user
    if not user.is_superuser:
        return redirect("tournaments:tournament_view", tournament_id)
    draft = get_object_or_404(Draft, pk=draft_id)
    services.pair_current_round(draft)
    return redirect("tournaments:tournament_view", tournament_id)


@login_required
def clear_history_view(request, tournament_id, draft_id):
    user = request.user
    if not user.is_superuser:
        return redirect("tournaments:tournament_view", tournament_id)
    draft = get_object_or_404(Draft, pk=draft_id)
    services.clear_histories(draft)
    return redirect("tournaments:tournament_view", tournament_id)


@login_required
def start_round_view(request, tournament_id, round_id):

    user = request.user
    if not user.is_superuser:
        return redirect("tournaments:tournament_view", tournament_id)
    round = get_object_or_404(Round, pk=round_id)
    round.round_timer_start = timezone.now()
    round.save()
    return redirect("tournaments:tournament_view", tournament_id)


@login_required
def stop_round_view(request, tournament_id, round_id):
    user = request.user
    if not user.is_superuser:
        return redirect("tournaments:tournament_view", tournament_id)
    round = get_object_or_404(Round, pk=round_id)
    round.round_timer_start = None
    round.save()
    return redirect("tournaments:tournament_view", tournament_id)

@login_required
def games_for_draft(request, tournament_id, draft_id):
    draft = get_object_or_404(Draft, pk=draft_id)
    round = Round.objects.filter(draft=draft).order_by("-round_idx").first()
    games = Game.objects.filter(round=round)
    game_results = [
        {
            "id": game.id,
            "table": game.table,
            "player1": game.player1.player.user.name,
            "player2": game.player2.player.user.name,
            "result": game.game_result_formatted(),
            "result_confirmed": game.result_confirmed,
        }
        for game in games
    ]
    return JsonResponse({"games": game_results})

@login_required
def game_results(request):
    games = Game.objects.all()
    game_results = [
        {
            "id": game.id,
            "table": game.table,
            "player1": game.player1.player.user.name,
            "player2": game.player2.player.user.name,
            "result": game.game_result_formatted(),
            "result_confirmed": game.result_confirmed,
        }
        for game in games
    ]
    return JsonResponse({"games": game_results})


@login_required
def my_current_match(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    user = request.user
    try:
        player = Player.objects.get(user=user)
    except Player.DoesNotExist:
        return JsonResponse(
            {"error": "No player exists for the current user."}, status=404
        )

    try:
        enrollments = Enrollment.objects.get(player=player, tournament=tournament)
    except Enrollment.DoesNotExist:
        return JsonResponse(
            {"error": "Player is not enrolled in this tournament."}, status=404
        )

    context = {
        "tournament": tournament,
        "enrollments": enrollments,
    }

    return render(request, "tournaments/current_match.html", context=context)


@login_required
def current_draft(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    user = request.user

    try:
        player = Player.objects.get(user=user)
    except Player.DoesNotExist:
        return JsonResponse(
            {"error": "No player exists for the current user."}, status=404
        )

    try:
        enrollment = Enrollment.objects.get(player=player, tournament=tournament)
    except Enrollment.DoesNotExist:
        return JsonResponse(
            {"error": "Player is not enrolled in this tournament."}, status=404
        )
    try:
        drafts = Draft.objects.filter(enrollments__in=[enrollment.id]).order_by(
            "-phase"
        )
    except Draft.DoesNotExist:
        return JsonResponse(
            {"error": "Player can't be found in any drafts."}, status=404
        )

    latest_draft = drafts.first()

    if latest_draft:
        latest_draft_data = {
            "id": latest_draft.id,
            "cube": latest_draft.cube.name,
            "cube_url": latest_draft.cube.url,
            "round_number": latest_draft.round_number,
        }
        return JsonResponse({"current_draft": latest_draft_data})
    else:
        return JsonResponse(
            {"error": "No drafts found for this player in the tournament."}, status=404
        )


@login_required
def current_game(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    user = request.user
    try:
        player = Player.objects.get(user=user)
    except Player.DoesNotExist:
        return JsonResponse(
            {"error": "No player exists for the current user."}, status=404
        )

    try:
        enrollment = Enrollment.objects.get(player=player, tournament=tournament)
    except Enrollment.DoesNotExist:
        return JsonResponse(
            {"error": "Player is not enrolled in this tournament."}, status=404
        )

    games = Game.objects.filter(Q(player1=enrollment) | Q(player2=enrollment)).order_by(
        "-round"
    )
    latest_game = games.first()

    player_role = 1
    if latest_game.player2 == enrollment:
        player_role = 2

    if latest_game:
        latest_game_data = {
            "id": latest_game.id,
            "table": latest_game.table,
            "player1": latest_game.player1.player.user.name,
            "player2": latest_game.player2.player.user.name,
            "game_formatted": latest_game.game_formatted(),
            "result_formatted": latest_game.game_result_formatted(),
            "result_confirmed": latest_game.result_confirmed,
            "player1_wins": latest_game.player1_wins,
            "player2_wins": latest_game.player2_wins,
            "reported_by": latest_game.result_reported_by,
            "player_role": player_role,
        }
        return JsonResponse({"current_game": latest_game_data})
    else:
        return JsonResponse(
            {"error": "No games found for this player in the tournament."}, status=404
        )


@csrf_exempt
@login_required
def report_result(request):
    if request.method == "POST":
        data = json.loads(request.body)
        tournament_id = data.get("tournament_id")
        player1_wins = data.get("player1_wins")
        player2_wins = data.get("player2_wins")

        tournament = get_object_or_404(Tournament, pk=tournament_id)
        user = request.user
        player = Player.objects.get(user=user)

        try:
            enrollment = Enrollment.objects.get(player=player, tournament=tournament)
        except Enrollment.DoesNotExist:
            return JsonResponse(
                {"error": "Player is not enrolled in this tournament."}, status=404
            )

        try:
            draft = (
                Draft.objects.get(enrollments__in=[enrollment.id])
            )
        except Draft.DoesNotExist:
            return JsonResponse(
                {"error": "Could not get current draft for tournament."}, status=404
            )

        try:
            round = Round.objects.get(draft=draft)
        except Round.DoesNotExist:
            return JsonResponse(
                {"error": "Could not get current round for tournament."}, status=404
            )

        game = Game.objects.get(
            Q(player1=enrollment) | Q(player2=enrollment), round=round
        )

        reported_by = 1
        if game.player2 == enrollment:
            reported_by = 2

        if game:
            game.player1_wins = player1_wins
            game.player2_wins = player2_wins
            game.result = f"{player1_wins}-{player2_wins}"
            game.result_reported_by = reported_by
            game.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"error": "Game not found"}, status=404)

    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
@login_required
def confirm_result(request):
    if request.method == "POST":
        data = json.loads(request.body)
        tournament_id = data.get("tournament_id")

        tournament = get_object_or_404(Tournament, pk=tournament_id)
        user = request.user
        player = Player.objects.get(user=user)

        try:
            enrollment = Enrollment.objects.get(player=player, tournament=tournament)
        except Enrollment.DoesNotExist:
            return JsonResponse(
                {"error": "Player is not enrolled in this tournament."}, status=404
            )

        try:
            draft = (
                Draft.objects.get(enrollments__in=[enrollment.id])
            )
        except Draft.DoesNotExist:
            return JsonResponse(
                {"error": "Could not get current draft for tournament."}, status=404
            )

        try:
            round = Round.objects.get(draft=draft)
        except Round.DoesNotExist:
            return JsonResponse(
                {"error": "Could not get current round for tournament."}, status=404
            )

        game = (
            Game.objects.filter(
                Q(player1=enrollment) | Q(player2=enrollment), round=round
            )
            .order_by("-round")
            .first()
        )
        if game:
            game.result_confirmed = True
            services.update_result(game.id, game.player1_wins, game.player2_wins)
            game.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"error": "Game not found"}, status=404)

    return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required
def finish_round(request, tournament_id, draft_id):
    if request.user.is_superuser:
        draft = get_object_or_404(Draft, pk=draft_id)
        services.finish_round(draft)
    return redirect("tournaments:standings", tournament_id, draft_id)

@login_required
def standings(request, tournament_id, draft_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    draft = get_object_or_404(Draft, pk=draft_id)
    round = Round.objects.filter(draft=draft).order_by("-round_idx")[1]
    sorted_players = services.make_standings(draft)
    context = {
        "tournament": tournament,
        "players": sorted_players,
        "draft": draft,
        "round": round,
    }
    return render(request, "tournaments/standings.html", context)

@login_required
def sync(request, tournament_id, draft_id):
    draft = get_object_or_404(Draft, pk=draft_id)
    round = Round.objects.filter(draft=draft).order_by("-round_idx").first()
    games = Game.objects.filter(round=round)
    for game in games:
        services.update_result(game.id, game.player1_wins, game.player2_wins)
    return redirect("tournaments:standings", tournament_id, draft_id)