from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from django.db.models import Prefetch
from django.utils.translation import gettext as _

from .models import Player, Enrollment, Draft, Game, Tournament, SideEvent, Image, Round
from . import services


def player(user, force_update=False):
    """Gets the player corresponding to the current user.
    Pulls from the cache if available, queries the DB if not.
    """
    if not force_update:
        player = cache.get(f"player_{user.id}")
        if player:
            return player
    player = Player.objects.select_related("user").get(user=user)
    if not player:
        raise ValueError("No player found for current user")

    cache.set(f"player_{user.id}", player, 60)
    return player


def all_enrollments(player, uid, force_update=False):
    """Gets all enrollments corresponding to the given player.
    Pulls from the cache if available, queries the DB if not.
    """
    if not force_update:
        enrollments = cache.get(f"enrollments_{uid}")
        if enrollments:
            return enrollments
    enrollments = Enrollment.objects.filter(player=player).select_related("tournament")

    if not enrollments:
        raise ValueError("No enrollments found for given player.")

    cache.set(
        f"enrollments_{uid}", enrollments, 300
    )  # Cache enrollments object for 5 minutes
    return enrollments

def all_tournaments(player, uid, force_update=False):
    """Gets all enrollments corresponding to the given player.
    Pulls from the cache if available, queries the DB if not.
    """
    if not force_update:
        tournaments = cache.get(f"tournaments_{uid}")
        if tournaments:
            return tournaments
    tournaments = Tournament.objects.filter(enrollment__player=player).distinct()

    if not tournaments:
        raise ValueError("No enrollments found for given player.")

    cache.set(
        f"tournaments_{uid}", tournaments, 300
    )  # Cache enrollments object for 5 minutes
    return tournaments

def enrollment_from_tournament(tournament, player, force_update=False):
    if not force_update:
        current_enroll = cache.get(f"tournament_enroll_{player.user.id}")
        if current_enroll:
            return current_enroll
    current_enroll = Enrollment.objects.get(tournament=tournament, player=player)
    cache.set(
        f"current_enroll_{player.user.id}", current_enroll, 300
    )  # Cache enrollments for 5 minutes
    return current_enroll



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
        Draft.objects.filter(Q(finished=False) & Q(enrollments=current_enrollment))
        .select_related("phase")
        .order_by("phase__phase_idx")
        .first()
    )

    if not draft:
        raise ValueError(_("As soon as one of your drafts starts, you will be able to see it here."))

    cache.set(f"draft_{uid}", draft, 120)  # Cache draft object for 2 minutes
    return draft


def non_player_games(current_enrollment, current_round, uid, force_update=False):
    if not force_update:
        non_player_games = cache.get(f"non_player_games{uid}")
        if non_player_games:
            return non_player_games

    non_player_games = Game.objects.filter(
        ~Q(player1=current_enrollment)
        & ~Q(player2=current_enrollment)
        & Q(round=current_round)
    ).order_by("table")

    if not non_player_games:
        raise ValueError("No other pairings found for given user.")
    cache.set(
        f"non_player_games{uid}", non_player_games, 120
    )  # Cache other pairings for 2 minutes
    return non_player_games


def bye_this_round(current_enrollment, current_draft, force_update=False):
    if not force_update:
        bye_this_round = cache.get(f"bye_this_round_{current_draft.id}")
        if bye_this_round:
            return bye_this_round

    try:
        bye_this_round = current_draft.enrollments.get(bye_this_round=True)
        cache.set(f"bye_this_round_{current_draft.id}", bye_this_round, 120)
        return (
            bye_this_round.player.user.name
            if bye_this_round != current_enrollment
            else False
        )
    except Enrollment.DoesNotExist:
        return False


def latest_event(force_update=False, sideevent=True):
    if not force_update:
        event = cache.get("latest_event")
        if event:
            return event

    if sideevent:
        event = Tournament.objects.all().order_by("-start_datetime").first()
    else:
        event = (
            Tournament.objects.filter(sideevent__isnull=True)
            .order_by("-start_datetime")
            .first()
        )
    if not event:
        raise ValueError("No events found.")
    cache.set("latest_event", event, 300)
    return event


def timetable(current_enrollment, uid, force_update=False):
    if not force_update:
        timetable = cache.get(f"timetable_{uid}")
        if timetable:
            return timetable

    timetable = Draft.objects.filter(enrollments=current_enrollment).order_by("phase")
    if not timetable:
        raise ValueError("No upcoming drafts found for given player.")
    cache.set(f"timetable_{uid}", timetable, 120)
    return timetable


def available_side_events(player, event, uid, force_update=False):
    if not force_update:
        side_events = cache.get(f"side_events_{uid}")
        if side_events:
            return side_events

    # Get all tournaments the player is enrolled in
    enrolled_tournament_ids = Enrollment.objects.filter(player=player).values_list(
        "tournament_id", flat=True
    )

    # Get all SideEvents where the player is not enrolled
    now = timezone.now()
    side_events = SideEvent.objects.exclude(
        Q(id__in=enrolled_tournament_ids) | Q(start_datetime__lt=now)
    ).order_by("start_datetime")
    if not side_events:
        raise ValueError("No available side events found for given player.")
    cache.set(f"side_events{uid}", side_events, 300)
    return list(side_events)


def images(user, draft, checkin: bool):
    images = Image.objects.filter(user=user, draft_idx=draft.id, checkin=checkin)
    return images


def enroll_for_side_event(user, side_event):
    user_player = player(user)

    if Enrollment.objects.filter(player=user_player, tournament=side_event).exists():
        raise ValueError("User is already enrolled in this side event.")
    if timezone.now() >= side_event.start_datetime:
        raise ValueError("Event has already started")
    Enrollment.objects.create(
        tournament=side_event, player=user_player, registration_finished=True
    )


def player_timetable(player, uid, event, force_update=False):
    if not force_update:
        timetable = cache.get(f"timetable_{uid}")
        if timetable:
            return timetable

    player_enrolls = all_enrollments(player, uid, force_update)
    current_enroll = current_enrollment(player_enrolls, uid, force_update)

    timetable = Draft.objects.filter(
        enrollments=current_enroll, finished=False, started=False
    ).order_by("phase__phase_idx")

    if not timetable:
        raise ValueError("No drafts found for current user.")

    cache.set(f"timetable_{uid}", timetable, 120)
    return timetable


def report_result(match_id, player1_wins, player2_wins, reporting_player, admin=False):
    if int(player1_wins) + int(player2_wins) > 3:
        raise ValueError("Error: Please enter a valid game result.")

    match = cache.get(f"match_{match_id}")
    if not match:
        match = Game.objects.get(pk=match_id)
        if not match:
            raise ValueError("Error: Match not found")
        cache.set(f"match_{match_id}", match, 300)

    match.player1_wins = int(player1_wins)
    match.player2_wins = int(player2_wins)
    match.result = f"{player1_wins}-{player2_wins}"
    if not admin:
        match.result_reported_by = reporting_player.user.name
    else:
        match.result_reported_by = "Admin"
        match.result_confirmed = True
        services.update_result(match, match.player1_wins, match.player2_wins)
    match.save()


def active_drafts_for_event(event, force_update=False):
    if not force_update:
        drafts = cache.get(f"active_drafts_{event.id}")
        if drafts:
            return drafts

    drafts = Draft.objects.filter(
        phase__tournament=event,
        phase__started=True,
        phase__finished=False,
        finished=False,
    ).order_by("-phase__phase_idx")

    if drafts:
        cache.set(f"active_drafts_{event.id}", drafts, 120)
        return drafts
    raise ValueError("No active drafts found")


def get_tournament(tournament_id=None, tournament_slug=None, force_update=False):
    if not force_update:
        if tournament_id:
            tournament = cache.get(f"tournament_{tournament_id}")
        elif tournament_slug:
            tournament = cache.get(f"tournament_{tournament_slug}")
        if tournament:
            return tournament

    if tournament_id:
        try:
            tournament = SideEvent.objects.get(pk=tournament_id)
        except SideEvent.DoesNotExist:
            tournament = Tournament.objects.get(pk=tournament_id)
    elif tournament_slug:
        try:
            tournament = SideEvent.objects.get(slug=tournament_slug)
        except SideEvent.DoesNotExist:
            tournament = Tournament.objects.get(slug=tournament_slug)

    if tournament_id:
        cache.set(f"tournament_{tournament_id}", tournament, 300)
    elif tournament_slug:
        cache.set(f"tournament_{tournament_slug}", tournament, 300)
    return tournament

def draft_from_id(draft_id, force_update=False):
    if not force_update:
        draft = cache.get(f"draft_{draft_id}")
        if draft:
            return draft

    draft = Draft.objects.get(pk=draft_id)
    if draft:
        cache.set(f"draft_{draft_id}", draft, 300)
        return draft
    raise ValueError("Draft for ID not found.")


def match_from_id(match_id, force_update=False):
    if not force_update:
        match = cache.get(f"match_{match_id}")
        if match:
            return match

    match = Game.objects.get(pk=match_id)
    if match:
        cache.set(f"match_{match_id}", match, 300)
        return match
    raise ValueError("Match for ID not found.")


def enrollments_for_tournament(tournament, force_update=False):
    if not force_update:
        enrollments = cache.get(f"tournament_enrollments_{tournament.id}")
        if enrollments:
            return enrollments

    enrollments = Enrollment.objects.filter(tournament=tournament).all()
    cache.set(f"tournament_enrollments_{tournament.id}", enrollments, 60)
    return enrollments


def current_round(current_draft, force_update=False):
    if not force_update:
        current_round = cache.get(f"current_round_{current_draft.id}")
        if current_round:
            return current_round

    current_round = (
        Round.objects.filter(draft=current_draft).order_by("-round_idx").first()
    )

    if current_round:
        cache.set(f"current_round_{current_draft.id}", current_round, 120)
        return current_round

    raise ValueError("Pairings will be shown here after the draft has finished.")


def current_match(current_enroll, current_round, uid, force_update=False):
    if not force_update:
        current_match = cache.get(f"current_match_{uid}")
        if current_match:
            return current_match

    try:
        current_match = Game.objects.get(
            Q(player1=current_enroll) | Q(player2=current_enroll),
            round=current_round,
        )
        cache.set(f"current_match_{uid}", current_match, 60)
        return current_match
    except Game.DoesNotExist:
        raise ValueError(f"Waiting for pairings for round {current_round.round_idx}.")


def player_enroll_for_tournament(player, tournament_id, uid, force_update=False):
    tournament = get_tournament(tournament_id, force_update)

    if not force_update:
        enrollment = cache.get(f"enrollment_{uid}")
        if enrollment:
            return enrollment

    enrollment = Enrollment.objects.get(tournament=tournament, player=player)
    if enrollment:
        cache.set(f"enrollment_{uid}", enrollment, 300)
        return enrollment
    raise ValueError("Enrollment in event for player not found.")


def admin_draft_prefetch(slug, force_update=False):
    if not force_update:
        draft = cache.get(f"admin_draft_{slug}")
        if draft:
            return draft

    draft = (
        Draft.objects.filter(slug=slug)
        .select_related("cube")
        .prefetch_related(
            Prefetch("enrollments__player__user", to_attr="enrolled_players"),
        ).first()
    )

    if draft:
        cache.set(f"admin_draft_{slug}", draft, 300)
        return draft
    raise ValueError("Draft for slug not found")


def admin_round_prefetch(draft, force_update=False):
    if not force_update:
        current_round = cache.get(f"admin_round_{draft.id}")
        if current_round:
            return current_round

    current_round = (
        Round.objects.filter(draft=draft)
        .order_by("-round_idx")
        .select_related("draft")
        .prefetch_related(
            Prefetch("game_set__player1__player__user"),
            Prefetch("game_set__player2__player__user"),
        )
        .first()
    )

    if current_round:
        cache.set(f'admin_round_{draft.id}', current_round, 60)
        return current_round
    raise ValueError("No current round found to prefetch for.")
