import json
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views import generic
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Tournament, Enrollment, Player, Game
from .services import pair_current_round, clear_histories, make_standings, update_result

class IndexView(generic.ListView):
    template_name = 'tournaments/index.html'
    context_object_name = 'all_tournaments'

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
            is_player_enrolled = event_enrollments.filter(player = player)
            if not is_player_enrolled:
                available_enrollments.append(event)
    except Player.DoesNotExist:
        available_enrollments = events
    print(f'There are {len(available_enrollments)} tournaments available for the current user.')
    return render(request, 'tournaments/all_events.html', {'available': available_enrollments})

@login_required
def my_events(request):
    user = request.user
    try:
        player = Player.objects.get(user=user)
        enrollments = Enrollment.objects.filter(player=player)
    except Player.DoesNotExist:
        enrollments = []  # Handle the case where the user is not a player
    return render(request, 'tournaments/my_events.html', {'enrollments': enrollments})

@login_required    
def tournament_view(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    enrollments = Enrollment.objects.filter(tournament=tournament)
    context = {
        'tournament': tournament,
        'enrollments': enrollments,
    }
    user = request.user
    if not user.is_superuser:
        return render(request, 'tournaments/tournament.html', context)
    return tournament_admin_view(request, context)
    
@login_required
def tournament_admin_view(request, context):
    games = Game.objects.filter(tournament=context['tournament'])
    context['games'] = games
    return render(request, 'tournaments/tournament_admin.html', context)

@login_required
def enroll_view(request, tournament_id):
    user = request.user
    player = Player.objects.get(user=user)
    tournament = get_object_or_404(Tournament, pk=tournament_id)

    # Catch duplicate enrollment attempts
    event_active_enrollments = Enrollment.objects.filter(tournament=tournament, player=player)
    if event_active_enrollments.exists():
        print('Redirecting already registered user.')
        return redirect('tournaments:all_events')

    context = {
        'user': user,
        'tournament': tournament,
    }
    return render(request, 'tournaments/enroll.html', context)

@login_required
def enroll_user_view(request, tournament_id):
    user = request.user
    player = Player.objects.get(user=user)
    tournament = get_object_or_404(Tournament, pk=tournament_id)

    Enrollment.objects.create(player=player, tournament=tournament)
    return redirect('tournaments:my_events')

@login_required
def pair_round_view(request, tournament_id):
    user = request.user
    if not user.is_superuser:
        return redirect('tournaments:tournament_view', tournament_id)
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    pair_current_round(tournament)
    return redirect('tournaments:tournament_view', tournament_id)

@login_required
def clear_history_view(request, tournament_id):
    user = request.user
    if not user.is_superuser:
        return redirect('tournaments:tournament_view', tournament_id)
    clear_histories(tournament_id)
    return redirect('tournaments:tournament_view', tournament_id)

@login_required
def start_round_view(request, tournament_id):
    user = request.user
    if not user.is_superuser:
        return redirect('tournaments:tournament_view', tournament_id)
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    tournament.round_timer_start = timezone.now()
    tournament.save()
    return redirect('tournaments:tournament_view', tournament_id)

@login_required
def stop_round_view(request, tournament_id):
    user = request.user
    if not user.is_superuser:
        return redirect('tournaments:tournament_view', tournament_id)
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    tournament.round_timer_start = None
    tournament.save()
    return redirect('tournaments:tournament_view', tournament_id)

def game_results(request):
    games = Game.objects.all().values('id', 'table', 'player1__player__user__username', 'player2__player__user__username', 'result')
    game_results = [
        {
            'id': game['id'],
            'table': game['table'],
            'player1': game['player1__player__user__username'],
            'player2': game['player2__player__user__username'],
            'result': game['result'] if game['result'] else "Pending"
        }
        for game in games
    ]
    return JsonResponse({'games': game_results})

@login_required
def my_current_match(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    user = request.user
    try:
        player = Player.objects.get(user=user)
    except Player.DoesNotExist:
        return JsonResponse({'error': 'No player exists for the current user.'}, status=404)
    
    try:
        enrollments = Enrollment.objects.get(player=player, tournament=tournament)
    except Enrollment.DoesNotExist:
        return JsonResponse({'error': 'Player is not enrolled in this tournament.'}, status=404)
    
    context = {
        'tournament': tournament,
        'enrollments': enrollments,
    }

    return render(request, 'tournaments/current_match.html', context=context)

@login_required
def current_game(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    user = request.user
    try:
        player = Player.objects.get(user=user)
    except Player.DoesNotExist:
        return JsonResponse({'error': 'No player exists for the current user.'}, status=404)
    
    try:
        enrollment = Enrollment.objects.get(player=player, tournament=tournament)
    except Enrollment.DoesNotExist:
        return JsonResponse({'error': 'Player is not enrolled in this tournament.'}, status=404)

    games = Game.objects.filter(Q(player1=enrollment) | Q(player2=enrollment)).order_by('-round')
    latest_game = games.first()

    player_role = 1
    if latest_game.player2 == enrollment:
        player_role = 2

    if latest_game:
        latest_game_data = {
            'id': latest_game.id,
            'table': latest_game.table,
            'player1': latest_game.player1.player.user.name,
            'player2': latest_game.player2.player.user.name,
            'game_formatted': latest_game.game_formatted(),
            'result_formatted': latest_game.game_result_formatted(),
            'result_confirmed': latest_game.result_confirmed,
            'player1_wins': latest_game.player1_wins,
            'player2_wins': latest_game.player2_wins,
            'reported_by': latest_game.result_reported_by,
            'player_role': player_role,
        }
        print(latest_game_data)
        return JsonResponse({'current_game': latest_game_data})
    else:
        return JsonResponse({'error': 'No games found for this player in the tournament.'}, status=404)
    
@csrf_exempt
@login_required
def report_result(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        tournament_id = data.get('tournament_id')
        player1_wins = data.get('player1_wins')
        player2_wins = data.get('player2_wins')

        tournament = get_object_or_404(Tournament, pk=tournament_id)
        user = request.user
        player = Player.objects.get(user=user)

        try:
            enrollment = Enrollment.objects.get(player=player, tournament=tournament)
        except Enrollment.DoesNotExist:
            return JsonResponse({'error': 'Player is not enrolled in this tournament.'}, status=404)
        
        game = Game.objects.filter(Q(player1=enrollment) | Q(player2=enrollment), tournament=tournament).order_by('-round').first()

        reported_by = 1
        if game.player2 == enrollment:
            reported_by = 2

        if game:
            game.player1_wins = player1_wins
            game.player2_wins = player2_wins
            game.result = f"{player1_wins}-{player2_wins}"
            game.result_reported_by = reported_by
            game.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Game not found'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
@login_required
def confirm_result(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        tournament_id = data.get('tournament_id')

        tournament = get_object_or_404(Tournament, pk=tournament_id)
        user = request.user
        player = Player.objects.get(user=user)

        try:
            enrollment = Enrollment.objects.get(player=player, tournament=tournament)
        except Enrollment.DoesNotExist:
            return JsonResponse({'error': 'Player is not enrolled in this tournament.'}, status=404)
        
        game = Game.objects.filter(Q(player1=enrollment) | Q(player2=enrollment), tournament=tournament).order_by('-round').first()
        if game:
            game.result_confirmed = True
            update_result(game.id, game.player1_wins, game.player2_wins)
            game.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Game not found'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def standings(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    sorted_players = make_standings(tournament)
    context = {
        'tournament': tournament,
        'players': sorted_players,
    }
    return render(request, "tournaments/standings.html", context)