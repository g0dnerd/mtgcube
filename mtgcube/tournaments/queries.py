from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from django.db.models import Prefetch
from django.utils.translation import gettext as _

from itertools import chain

from .models import Player, Enrollment, Draft, Game, Tournament, SideEvent, Image, Round


def player(user, force_update=False):
    """Gets the player corresponding to the current user.
    Pulls from the cache if available, queries the DB if not.
    """
    if not force_update:
        player = cache.get(f"player_{user.id}")
        if player:
            return player
    try:
        player = Player.objects.select_related("user").get(user=user)
    except Player.DoesNotExist:
        if not user.is_superuser:
            player = Player(user=user)
            player.save()
            cache.set(f"player_{user.id}", player, 60)
            return player
        raise ValueError("No player found for current user")

    cache.set(f"player_{user.id}", player, 60)
    return player


def available_tournaments(player, uid, force_update=False):
    """Gets all available tournaments corresponding to the given player.
    Pulls from the cache if available, queries the DB if not.
    """
    if not force_update:
        tournaments = cache.get(f"available_tournaments_{uid}")
        if tournaments:
            return tournaments

    # Get all tournaments the player is enrolled in
    enrolled_tournament_ids = Enrollment.objects.filter(player=player).values_list(
        "tournament_id", flat=True
    )

    now = timezone.now()
    if player:
        mains = (
            Tournament.objects.exclude(
                Q(id__in=enrolled_tournament_ids) | Q(start_datetime__lt=now)
            )
            .filter(sideevent__isnull=True)
            .distinct()
            .order_by("start_datetime")
        )
        sides = (
            SideEvent.objects.exclude(
                Q(id__in=enrolled_tournament_ids) | Q(start_datetime__lt=now)
            )
            .distinct()
            .order_by("start_datetime")
        )
    else:
        mains = (
            Tournament.objects.exclude(Q(start_datetime__lt=now))
            .filter(sideevent__isnull=True)
            .distinct()
            .order_by("start_datetime")
        )
        sides = (
            SideEvent.objects.exclude(Q(start_datetime__lt=now))
            .distinct()
            .order_by("start_datetime")
        )

    tournaments = list(chain(mains, sides))

    if not tournaments:
        raise ValueError("No available tournaments found for given player.")

    cache.set(
        f"available_tournaments_{uid}", tournaments, 300
    )  # Cache enrollments object for 5 minutes
    return tournaments


def enrolled_tournaments(player, uid, force_update=False):
    """Gets all enrollments corresponding to the given player.
    Pulls from the cache if available, queries the DB if not.
    """
    if not force_update:
        tournaments = cache.get(f"tournaments_{uid}")
        if tournaments:
            return tournaments

    now = timezone.now()
    if player:
        mains = (
            Tournament.objects.exclude(Q(start_datetime__lt=now))
            .filter(sideevent__isnull=True, enrollment__player=player)
            .distinct()
            .order_by("start_datetime")
        )
        sides = (
            SideEvent.objects.filter(enrollment__player=player)
            .distinct()
            .order_by("start_datetime")
        )
    else:
        mains = (
            Tournament.objects.filter(sideevent__isnull=True)
            .distinct()
            .order_by("start_datetime")
        )
        sides = SideEvent.objects.all().distinct().order_by("start_datetime")

    tournaments = list(chain(mains, sides))

    cache.set(
        f"tournaments_{uid}", tournaments, 300
    )  # Cache enrollments object for 5 minutes
    return tournaments


def enrollment_from_tournament(tournament, player, force_update=False):
    if not force_update:
        current_enroll = cache.get(
            f"tournament_enroll_{player.user.id}_{tournament.id}"
        )
        if current_enroll:
            return current_enroll
    current_enroll = Enrollment.objects.get(tournament=tournament, player=player)
    cache.set(
        f"current_enroll_{player.user.id}_{tournament.id}", current_enroll, 300
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
        raise ValueError(
            _("As soon as one of your drafts starts, you will be able to see it here.")
        )

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
            if bye_this_round != current_enrollment:
                return bye_this_round.player.user.name
        return False

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


def timetable(tournament, current_enrollment, uid, force_update=False):
    if not force_update:
        timetable = cache.get(f"timetable_{uid}_{tournament.id}")
        if timetable:
            return timetable

    timetable = Draft.objects.filter(
        phase__tournament=tournament, enrollments=current_enrollment
    ).order_by("phase")
    if not timetable:
        raise ValueError("No upcoming drafts found for given player.")
    cache.set(f"timetable_{uid}_{tournament.id}", timetable, 120)
    return timetable


def images(user, draft, checkin: bool):
    images = Image.objects.filter(user=user, draft_idx=draft.id, checkin=checkin)
    return images


def enroll_for_event(user, tournament):
    user_player = player(user)

    if tournament.signed_up >= tournament.player_capacity:
        raise ValueError("Event is full.")

    if Enrollment.objects.filter(player=user_player, tournament=tournament).exists():
        raise ValueError("User is already enrolled in this event.")
    if timezone.now() >= tournament.start_datetime:
        raise ValueError("Event has already started")

    try:
        tournament.tournament
        Enrollment.objects.create(
            tournament=tournament, player=user_player, registration_finished=True
        )
    except AttributeError:
        Enrollment.objects.create(
            tournament=tournament, player=user_player, registration_finished=False
        )

    tournament.signed_up += 1
    tournament.save()


def report_result(match, player1_wins, player2_wins, reporting_player, admin=False):
    if int(player1_wins) + int(player2_wins) > 3:
        raise ValueError("Error: Please enter a valid game result.")

    match.player1_wins = int(player1_wins)
    match.player2_wins = int(player2_wins)
    match.result = f"{player1_wins}-{player2_wins}"
    if not admin:
        match.result_reported_by = reporting_player.user.name
    else:
        match.result_reported_by = "Admin"
        match.result_confirmed = True
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


def get_draft(id=None, slug=None, force_update=False):
    if not force_update:
        if id:
            draft = cache.get(f"draft_{id}")
            if draft:
                return draft
        if slug:
            draft = cache.get(f"draft_{slug}")
            if draft:
                return draft

    try:
        if id:
            draft = Draft.objects.get(pk=id)
        if slug:
            draft = Draft.objects.get(slug=slug)
    except Draft.DoesNotExist:
        return None
    cache.set(f"draft_{id}", draft, 300)
    return draft


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


def current_round(current_draft, force_update=True):
    if not force_update:
        current_round = cache.get(f"current_round_{current_draft.id}")
        if current_round:
            return current_round

    current_round = (
        Round.objects.filter(draft=current_draft).order_by("-round_idx").first()
    )

    cache.set(f"current_round_{current_draft.id}", current_round, 120)
    return current_round


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
        return None


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
        cache.set(f"admin_round_{draft.id}", current_round, 60)
        return current_round
    raise ValueError("No current round found to prefetch for.")


def enrollment_match_history(enroll, tournament, force_update=False):
    if not force_update:
        matches = cache.get(f"match_history_{enroll.player.user.id}")
        if matches:
            return matches

    matches = Game.objects.filter(
        Q(player1=enroll) | Q(player2=enroll),
        round__draft__phase__tournament=tournament,
    )

    cache.set(f"match_history_{enroll.player.user.id}", matches, 300)
    return matches


def draft_standings(draft):
    rd = current_round(draft, force_update=True)
    rd_idx = rd.round_idx if not rd.finished else rd.round_idx + 1
    if not rd or rd_idx == 1 and not rd.finished:
        return None

    standings = cache.get(f"draft_standings_{draft.id}", version=rd_idx)
    if standings:
        return standings

    players = draft.enrollments.all()
    sorted_players = sorted(
        players,
        key=lambda x: (x.draft_score, x.draft_omw, x.draft_pgw, x.draft_ogw),
        reverse=True,
    )
    cache.set(
        f"draft_standings_{draft.id}",
        sorted_players,
        timeout=None,
        version=rd_idx,
    )
    return sorted_players


def tournament_standings(tournament, force_update=False):
    if tournament.current_round <= 1:
        return None
    if not force_update:
        standings = cache.get(
            f"tournament_standings_{tournament.id}",
            version=tournament.current_round
        )
        if standings:
            return standings

    players = enrollments_for_tournament(tournament, force_update)
    sorted_players = sorted(
        players, key=lambda x: (x.score, x.omw, x.pgw, x.ogw), reverse=True
    )
    cache.set(
        f'tournament_standings_{tournament.id}',
        sorted_players,
        timeout=None,
        version=tournament.current_round
    )
    return sorted_players
