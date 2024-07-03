from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views import generic

from .models import Tournament, Enrollment, Player

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