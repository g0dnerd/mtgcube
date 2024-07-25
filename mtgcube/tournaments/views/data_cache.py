from django.core.cache import cache
from django.db.models import Q

from ..models import Player, Enrollment, Draft, Game, Tournament


def player(user, force_update=False):
    """Gets the player corresponding to the current user.
    Pulls from the cache if available, queries the DB if not.
    """
    if not force_update:
        player = cache.get(f"player_{user.id}")
        if player:
            return player
    player = Player.objects.get(user=user)
    if not player:
        raise ValueError("No player found for current user")

    cache.set(f"player_{user.id}", player, 60)  # Cache player object for 1 minute
    return player


def all_enrollments(player, uid, force_update=False):
    """Gets all enrollments corresponding to the given player.
    Pulls from the cache if available, queries the DB if not.
    """
    if not force_update:
        enrollments = cache.get(f"enrollments_{uid}")
        if enrollments:
            return enrollments
    enrollments = Enrollment.objects.filter(player=player)

    if not enrollments:
        raise ValueError("No enrollments found for given player.")

    cache.set(
        f"enrollments_{uid}", enrollments, 300
    )  # Cache enrollments object for 5 minutes
    return enrollments


def current_enrollment(enrollments, uid, force_update=False):
    if not force_update:
        current_enroll = cache.get(f"current_enroll_{uid}")
        if current_enroll:
            return current_enroll
    current_enroll = enrollments.order_by("-enrolled_on").first()
    cache.set(
        f"current_enroll_{uid}", current_enroll, 300
    )  # Cache enrollments for 5 minutes
    return current_enroll


def current_draft(current_enrollment, uid, force_update=False):
    if not force_update:
        draft = cache.get(f"draft_{uid}")
        if draft:
            return draft
    draft = (
        Draft.objects.filter(
            ~Q(finished=True), enrollments__in=[current_enrollment]
        )
        .order_by("phase__phase_idx")
        .first()
    )

    if not draft:
        raise ValueError("No active draft found for given user.")

    cache.set(f"draft_{uid}", draft, 120)  # Cache draft object for 2 minutes
    return draft


def non_player_games(current_enrollment, current_round, uid, force_update=False):
    if not force_update:
        non_player_games = cache.get(f"non_player_games{uid}")
        if non_player_games:
            return non_player_games

    non_player_games = Game.objects.filter(
        ~(Q(player1=current_enrollment) | Q(player2=current_enrollment)),
        round=current_round,
    ).order_by("table")

    if not non_player_games:
        raise ValueError("No other pairings found for given user.")
    cache.set(
        f"non_player_game{uid}", non_player_games, 120
    )  # Cache other pairings for 2 minutes
    return non_player_games


def bye_this_round(current_enrollment, current_draft, force_update=False):
    if not force_update:
        bye_this_round = cache.get(f'bye_this_round_{current_draft.id}')
        if bye_this_round:
            return bye_this_round

    try:
        bye_this_round = current_draft.enrollments.get(bye_this_round=True)
        cache.set(f'bye_this_round_{current_draft.id}', bye_this_round, 120)
        if bye_this_round == current_enrollment:
            return False
        return bye_this_round.player.user.name
    except Enrollment.DoesNotExist:
        return False

def latest_event(force_update=False):
    if not force_update:
        event = cache.get('latest_event')
        if event:
            return event

    event = Tournament.objects.all().order_by("-start_datetime").first()
    if not event:
        raise ValueError("No events found.")
    cache.set('latest_event', event, 300)
    return event

def next_draft(current_enrollment, uid, force_update=False):
    if not force_update:
        next_draft = cache.get(f'next_draft_{uid}')
        if next_draft:
            return next_draft
    
    try:
        drafts = Draft.objects.filter(
            started=False, enrollments__in=[current_enrollment]
        ).order_by("-phase")
        next_draft = drafts[0]
        if current_draft == next_draft:
            raise IndexError
        cache.set(f'next_draft_{uid}', next_draft, 120)
        return next_draft
    except IndexError:
        raise ValueError("No upcoming draft found for given player.")
