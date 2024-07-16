import json
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
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
def admin_overview(request):
    user = request.user
    if not user.is_superuser:
        return redirect("pages/index.html")
    tournaments = Tournament.objects.all()
    return redirect('tournaments:tournament_view', tournaments)


@login_required
def event_dashboard(request):
    user = request.user
    if user.is_superuser:
        return redirect("tournaments:tournament_admin_view")
    try:
        player = Player.objects.get(user=user)
    except Player.DoesNotExist:
        return redirect("pages/home.html")
    try:
        enrollments = Enrollment.objects.filter(player=player)
    except Enrollment.DoesNotExist:
        return redirect("pages/home.html")
    latest_event = enrollments.order_by("-enrolled_on").first().tournament
    context = {
        "tournament": latest_event,
    }
    if not user.is_superuser:
        return render(request, "tournaments/event_dashboard.html", context)


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
def pair_round_view(request, tournament_id, draft_id):
    user = request.user
    if not user.is_superuser:
        return redirect("tournaments:tournament_view", tournament_id)
    draft = get_object_or_404(Draft, pk=draft_id)
    services.pair_current_round(draft)
    return redirect("tournaments:tournament_view", tournament_id)


@login_required
def clear_history(request, tournament_id, draft_id):
    user = request.user
    if not user.is_superuser:
        return redirect("tournaments:tournament_view", tournament_id)
    draft = get_object_or_404(Draft, pk=draft_id)
    services.clear_histories(draft)
    return redirect("tournaments:tournament_view", tournament_id)


@login_required
def start_round(request, tournament_id, draft_id):
    user = request.user
    if not user.is_superuser:
        return redirect("tournaments:tournament_view", tournament_id)
    draft = get_object_or_404(Draft, pk=draft_id)
    round = Round.objects.filter(draft=draft).order_by("-round_idx").first()
    round.started = True
    round.save()
    return redirect("tournaments:tournament_view", tournament_id)


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
def game_by_id(request, game_id):
    if game_id == 0:
        return JsonResponse({"error": "No valid game ID provided."}, status=404)
    game = get_object_or_404(Game, pk=game_id)

    round = game.round
    draft = round.draft
    phase = draft.phase
    tournament = phase.tournament

    user = request.user
    if not user.is_superuser:
        player = Player.objects.get(user=user)
        try:
            enrollment = get_object_or_404(
                Enrollment, player=player, tournament=tournament
            )
        except Enrollment.DoesNotExist:
            return JsonResponse(
                {"error": "Player is not enrolled in this tournament."}, status=404
            )
        player_role = 1
        if game.player2 == enrollment:
            player_role = 2
    else:
        player_role = 0

    return JsonResponse(
        {
            "id": game.id,
            "table": game.table,
            "player1": game.player1.player.user.name,
            "player2": game.player2.player.user.name,
            "result": game.game_result_formatted(),
            "result_confirmed": game.result_confirmed,
            "player1_wins": game.player1_wins,
            "player2_wins": game.player2_wins,
            "reported_by": game.result_reported_by,
            "player_role": player_role,
        }
    )


@login_required
def other_pairings(request, tournament_id):
    user = request.user
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    player = get_object_or_404(Player, user=user)
    enrollment = get_object_or_404(Enrollment, player=player, tournament=tournament)
    drafts = Draft.objects.filter(enrollments__in=[enrollment])

    round = Round.objects.filter(draft__in=[drafts]).order_by("-round_idx").first()
    games = Game.objects.filter(round=round)
    non_player_games = games.filter(~(Q(player1=enrollment) | Q(player2=enrollment)))

    return JsonResponse({"pairings": [
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
    ]})


@login_required
def current_match(request, tournament_id):
    user = request.user
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    player = get_object_or_404(Player, user=user)
    enrollment = get_object_or_404(Enrollment, player=player, tournament=tournament)

    game_id = (
        Game.objects.filter(Q(player1=enrollment) | Q(player2=enrollment))
        .order_by("-round")
        .first()
        .id
    )

    return redirect("tournaments:game_by_id", game_id)


@login_required
def current_draft_view(request, tournament_id, draft_id):
    user = request.user
    draft = get_object_or_404(Draft, pk=draft_id)
    player = get_object_or_404(Player, user=user)
    enrollment = get_object_or_404(Enrollment, player=player, draft__in=[draft])
    game = (
        Game.objects.filter(Q(player1=enrollment) | Q(player2=enrollment))
        .order_by("-round")
        .first()
    )
    game_id = game.id if game else 0
    draft_json = {
        "id": draft.id,
        "phase": draft.phase.phase_idx,
        "cube": draft.cube.name,
        "cube_url": draft.cube.url,
    }
    context = {"tournament_id": tournament_id, "draft": draft_json, "game_id": game_id}

    return render(request, "tournaments/current_draft.html", context=context)


@login_required
def draft_standings(request, tournament_id, draft_id):
    draft = get_object_or_404(Draft, pk=draft_id)
    current_round = Round.objects.filter(draft=draft).order_by("-round_idx").first()
    if current_round.round_idx == 1 and not current_round.finished:
        return JsonResponse({"error": "Draft has no standings yet."}, status=200)
    sorted_players = services.standings(draft, update=False)
    standings_out = [
        {
            "name": enrollment.player.user.name,
            "score": enrollment.score,
            "omw": enrollment.omw,
            "pgw": enrollment.pgw,
            "ogw": enrollment.ogw,
        }
        for enrollment in sorted_players
    ]
    return JsonResponse({"standings": standings_out})


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
        drafts = Draft.objects.filter(started=True, enrollments__in=[enrollment.id]).order_by(
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
def next_draft(request, tournament_id):
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
        drafts = Draft.objects.filter(started=False, enrollments__in=[enrollment.id]).order_by(
            "-phase"
        )
    except Draft.DoesNotExist:
        return JsonResponse(
            {"error": "No upcoming draft found."}, status=200
        )
    
    next_draft = drafts[0]
    next_draft_data = {
        "id": next_draft.id,
        "cube": next_draft.cube.name,
        "cube_url": next_draft.cube.url,
        "round_number": next_draft.round_number,
    }
    return JsonResponse({"current_draft": next_draft_data})


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
            draft = Draft.objects.get(enrollments__in=[enrollment.id])
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
            draft = Draft.objects.get(enrollments__in=[enrollment.id])
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
    return redirect("tournaments:standings_view", tournament_id, draft_id)


@login_required
def sync(request, tournament_id, draft_id):
    draft = get_object_or_404(Draft, pk=draft_id)
    round = Round.objects.filter(draft=draft).order_by("-round_idx").first()
    games = Game.objects.filter(round=round)
    for game in games:
        services.update_result(game.id, game.player1_wins, game.player2_wins)
    return redirect("tournaments:standings_view", tournament_id, draft_id)


@login_required
def seat_draft(request, tournament_id, draft_id):
    user = request.user
    if not user.is_superuser:
        return redirect("tournaments:current_draft_view", tournament_id, draft_id)

    draft = get_object_or_404(Draft, pk=draft_id)
    if not draft.seated:
        services.seatings(draft)
    return redirect("tournaments:tournament_view", tournament_id)


@login_required
def seatings(request, tournament_id, draft_id):
    draft = get_object_or_404(Draft, pk=draft_id)
    round = Round.objects.filter(draft=draft).order_by("-round_idx").first()
    if round.started:
        print("No seatings because draft already started.")
        return JsonResponse(
            {
                "error": f"Not returning seatings because draft is already in round {round.round_idx}"
            }
        )
    sorted_players = list(Enrollment.objects.filter(draft=draft).order_by("seat"))
    seatings_out = [
        {
            "seat": player.seat,
            "id": player.id,
            "name": player.player.user.name,
        }
        for player in sorted_players
    ]
    return JsonResponse({"seatings": seatings_out})

@login_required
def announcement(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    if tournament.announcement:
        return JsonResponse(
            {
                "announcement": tournament.announcement
            }
        )
    return JsonResponse(
        {
            "error": "no announcement"
        }
    )

@login_required
def signup_status(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    user = request.user
    player = Player.objects.get(user=user)
    try:
        enrollment = Enrollment.objects.get(player=player, tournament=tournament)
    except Enrollment.DoesNotExist:
        return redirect("pages/home.html")
    return JsonResponse(
        {
            "status": enrollment.registration_finished
        }
    )