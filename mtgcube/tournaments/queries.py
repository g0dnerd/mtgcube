from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from django.db.models import Prefetch

from itertools import chain

from .models import (
    Player,
    Enrollment,
    Draft,
    Game,
    Tournament,
    SideEvent,
    Image,
    Round,
    Phase,
)

User = get_user_model()


def get_or_set_cache(key, value_func, timeout=300, force_update=False):
    """Helper function to get an item from the cache, or set it if it doesn't exist."""
    if not force_update:
        cached_value = cache.get(key)
        if cached_value:
            print(f"Using cached value for {key}")
            return cached_value
    value = value_func()
    cache.set(key, value, timeout)
    return value


def get_player(user, force_update=False):
    """Gets the player corresponding to the current user by ID."""
    cache_key = f"player_{user.id}"

    def fetch_player():
        if user.is_superuser:
            return None
        try:
            player = Player.objects.select_related("user").get(user=user)
        except Player.DoesNotExist:
            if not user.is_superuser:
                player = Player(user=user)
                player.save()
        return player

    return get_or_set_cache(cache_key, fetch_player, 300, force_update)


def available_tournaments(player, force_update=False):
    """Gets all available tournaments for the given player."""
    if player:
        cache_key = f"available_tournaments_{player.user.id}"
    else:
        cache_key = "available_tournaments_admin"

    def fetch_available_tournaments():
        # Get all tournaments the player is enrolled in

        now = timezone.now()
        if player:
            enrolled_tournament_ids = Enrollment.objects.filter(
                player=player
            ).values_list("tournament_id", flat=True)
            mains = (
                Tournament.objects.exclude(
                    Q(id__in=enrolled_tournament_ids) | Q(end_datetime__lt=now)
                )
                .filter(sideevent__isnull=True, public=True)
                .distinct()
                .order_by("start_datetime")
            )
            sides = (
                SideEvent.objects.exclude(
                    Q(id__in=enrolled_tournament_ids) | Q(end_datetime__lt=now)
                )
                .filter(public=True)
                .distinct()
                .order_by("start_datetime")
            )
        else:
            mains = (
                Tournament.objects.exclude(Q(end_datetime__lt=now))
                .filter(sideevent__isnull=True)
                .distinct()
                .order_by("start_datetime")
            )
            sides = (
                SideEvent.objects.exclude(Q(end_datetime__lt=now))
                .distinct()
                .order_by("start_datetime")
            )

        return list(chain(mains, sides))

    return get_or_set_cache(cache_key, fetch_available_tournaments, 300, force_update)


def enrolled_tournaments(player, force_update=False):
    """Gets all distinct tournaments from the enrollments for the given player."""
    if player:
        cache_key = f"enrolled_tournaments_{player.user.id}"
    else:
        cache_key = "enrolled_tournaments_admin"

    def fetch_enrolled_tournaments():
        now = timezone.now()
        if player:
            mains = (
                Tournament.objects.filter(
                    sideevent__isnull=True, enrollment__player=player
                )
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

        return list(chain(mains, sides))

    return get_or_set_cache(cache_key, fetch_enrolled_tournaments, 300, force_update)


def enrollment_from_tournament(tournament, player, force_update=True):
    """Gets the enrollment for the given tournament and player."""
    cache_key = f"tournament_enroll_{player.user.id}_{tournament.id}"

    def fetch_enrollment():
        try:
            return Enrollment.objects.get(tournament=tournament, player=player)
        except Enrollment.DoesNotExist:
            return None

    return get_or_set_cache(cache_key, fetch_enrollment, 300, force_update)


def current_draft(current_enrollment):
    """Gets the currently active draft for the given player."""
    phase = active_phase(current_enrollment.tournament, force_update=True)
    if not phase:
        return None
    cache_key = f"current_draft_{current_enrollment.id}_{phase.phase_idx}"

    def fetch_current_draft():
        try:
            draft = Draft.objects.get(
                Q(enrollments=current_enrollment),
                phase=phase,
                phase__finished=False,
                phase__started=True,
            )
        except Draft.DoesNotExist:
            return None
        return draft

    return get_or_set_cache(cache_key, fetch_current_draft, timeout=None)


def non_player_games(current_enrollment, current_round):
    """Returns all active matches in the current draft that the player is not part of."""
    cache_key = f"non_player_games{current_enrollment.id}_{current_round.round_idx}"

    def fetch_non_player_games():
        non_player_games = Game.objects.filter(
            ~Q(player1=current_enrollment)
            & ~Q(player2=current_enrollment)
            & Q(round=current_round)
        ).order_by("table")
        return None if not non_player_games else non_player_games

    return get_or_set_cache(cache_key, fetch_non_player_games, timeout=None)


def bye_this_round(draft: Draft, current_enrollment=None):
    """Checks if the current draft has a bye this round.
    If an enrollment is given, checks if the current enrollment is the bye this round.
    """
    rd = current_round(draft, force_update=True)
    if not rd:
        return False if current_enrollment else None
    cache_key = f"bye_this_round_{draft.id}_{rd.round_idx}"

    def fetch_bye_this_round():
        try:
            bye_this_round = draft.enrollments.get(bye_this_round=True)
            if current_enrollment:
                if bye_this_round != current_enrollment:
                    return False
            return bye_this_round
        except Enrollment.DoesNotExist:
            return None

    return get_or_set_cache(cache_key, fetch_bye_this_round, None)


def timetable(tournament, current_enrollment, force_update=False):
    cache_key = f"timetable_{current_enrollment.id}"

    def fetch_timetable():
        timetable = Draft.objects.filter(
            phase__tournament=tournament, enrollments=current_enrollment
        ).order_by("phase")
        return None if not timetable else timetable

    return get_or_set_cache(cache_key, fetch_timetable, 120, force_update)


def images(user, draft, checkin: bool):
    images = Image.objects.filter(user=user, draft_idx=draft.id, checkin=checkin)
    return images


def active_drafts_for_tournament(event, force_update=False):
    """Returns all active drafts for the given tournament."""
    phase = active_phase(event, force_update=True)
    if not phase:
        return None
    cache_key = f"active_drafts_{event.id}_{phase.phase_idx}"

    def fetch_active_drafts():
        d = Draft.objects.filter(
            phase__tournament=event,
            phase__started=True,
            phase__finished=False,
            finished=False,
            phase=phase,
        )
        return None if not d else d

    return get_or_set_cache(cache_key, fetch_active_drafts, 300, force_update)


def get_tournament(id=None, slug=None, force_update=True):
    """Returns the tournament with the given id or slug."""
    cache_key = f"tournament_{id}" if id else f"tournament_{slug}"

    def fetch_tournament():
        if id:
            try:
                tournament = SideEvent.objects.get(pk=id)
            except SideEvent.DoesNotExist:
                try:
                    tournament = Tournament.objects.get(pk=id)
                except Tournament.DoesNotExist:
                    return None
        elif slug:
            try:
                tournament = SideEvent.objects.get(slug=slug)
            except SideEvent.DoesNotExist:
                try:
                    tournament = Tournament.objects.get(slug=slug)
                except Tournament.DoesNotExist:
                    return None
        return tournament

    return get_or_set_cache(cache_key, fetch_tournament, 300, force_update)


def get_draft(id=None, slug=None, force_update=True):
    """Returns the draft with the given id or slug."""
    cache_key = f"draft_{id}" if id else f"draft_{slug}"

    def fetch_draft():
        if id:
            try:
                draft = Draft.objects.get(pk=id)
            except Draft.DoesNotExist:
                return None
        elif slug:
            try:
                draft = Draft.objects.get(slug=slug)
            except Draft.DoesNotExist:
                return None
        return draft

    return get_or_set_cache(cache_key, fetch_draft, 60, force_update)


def matches_from_draft(draft, current_round, force_update=True):
    """Returns all matches in the given draft."""
    cache_key = f"matches_{draft.id}_{current_round.round_idx}"

    def fetch_matches():
        m = Game.objects.filter(round__draft=draft).order_by("table")
        return None if not m else m

    return get_or_set_cache(cache_key, fetch_matches, 30, force_update)


def get_match(match_id, force_update=True):
    """Returns the match with the given id."""
    cache_key = f"match_{match_id}"

    def fetch_match():
        try:
            return Game.objects.get(pk=match_id)
        except Game.DoesNotExist:
            return None

    return get_or_set_cache(cache_key, fetch_match, 30, force_update)


def enrollments_for_tournament(tournament, force_update=False):
    """Returns all enrollments for the given tournament."""
    cache_key = f"tournament_enrollments_{tournament.id}"

    def fetch_enrollments():
        # Get all enrollments for the given tournament that are also enrolled in a draft for the same tournament
        enrollments = Enrollment.objects.filter(tournament=tournament)

        # Get all enrollments for the given tournament that are also enrolled in a draft for the same tournament
        drafts = Draft.objects.filter(enrollments__in=enrollments)
        enrollments = enrollments.filter(draft__in=drafts).distinct()

        return None if not enrollments else enrollments

    return get_or_set_cache(cache_key, fetch_enrollments, 60, force_update)


def enrolled_users(tournament, force_update=False):
    """Returns all users that are enrolled in the given tournament."""
    cache_key = f"enrolled_users_{tournament.id}"

    def fetch_enrolled():
        enrollments = Enrollment.objects.filter(tournament=tournament).select_related(
            "player__user"
        )

        users = [e.player.user for e in enrollments]
        return users

    return get_or_set_cache(cache_key, fetch_enrolled, 60, force_update)


def not_enrolled_in_tournament(tournament, force_update=False):
    """Returns all users that are not enrolled in the given tournament."""
    cache_key = f"not_enrolled_in_tournament_{tournament.id}"

    def fetch_not_enrolled():
        enrolled = enrolled_users(tournament, force_update=True)
        return User.objects.filter(is_superuser=False).exclude(
            pk__in=[e.pk for e in enrolled]
        )

    return get_or_set_cache(cache_key, fetch_not_enrolled, 60, force_update)


def current_round(current_draft, force_update=False):
    """Returns the current round for the given draft."""
    cache_key = f"current_round_{current_draft.id}"

    def fetch_current_round():
        try:
            rd = (
                Round.objects.filter(draft=current_draft).order_by("-round_idx").first()
            )
        except Round.DoesNotExist:
            return None
        return rd

    return get_or_set_cache(cache_key, fetch_current_round, 30, force_update)


def current_match(current_enroll, current_round, force_update=True):
    """Returns the current match for the given enrollment and round."""
    cache_key = (
        f"current_match_{current_enroll.player.user.id}_{current_round.round_idx}"
    )

    def fetch_current_match():
        match = Game.objects.filter(
            Q(player1=current_enroll) | Q(player2=current_enroll),
            round=current_round,
        ).first()
        return None if not match else match

    return get_or_set_cache(cache_key, fetch_current_match, 300, force_update)


def admin_round_prefetch(draft, force_update=False):
    """Returns the current round for the given draft and prefetches the games."""
    cache_key = f"admin_round_{draft.id}"

    def fetch_current_round_prefetch():
        rd = (
            Round.objects.filter(draft=draft)
            .order_by("-round_idx")
            .select_related("draft")
            .prefetch_related(
                Prefetch("game_set__player1__player__user"),
                Prefetch("game_set__player2__player__user"),
            )
            .first()
        )
        return None if not rd else rd

    return get_or_set_cache(cache_key, fetch_current_round_prefetch, 30, force_update)


def enrollment_match_history(enroll, tournament, force_update=False):
    """Gets all matches the given enrollment has played in the given tournament."""
    cache_key = f"match_history_{enroll.player.user.id}"

    def fetch_match_history():
        return Game.objects.filter(
            Q(player1=enroll) | Q(player2=enroll),
            round__draft__phase__tournament=tournament,
        )

    return get_or_set_cache(cache_key, fetch_match_history, 300, force_update)


def draft_standings(draft):
    """Returns the current round's standings for the given draft."""
    rd = current_round(draft, force_update=True)
    if not rd or rd.round_idx == 1 and not rd.finished:
        return None
    rd_idx = rd.round_idx - 1 if not rd.finished else rd.round_idx
    cache_key = f"draft_standings_{draft.id}_{rd_idx}"

    def fetch_draft_standings():
        players = draft.enrollments.all()
        sorted_players = sorted(
            players,
            key=lambda x: (
                x.draft_score,
                x.draft_omw,
                x.draft_pgw,
                x.draft_ogw,
                x.player.user.name,
            ),
            reverse=True,
        )

        standings_out = [
            {
                "name": enrollment.player.user.name,
                "score": enrollment.draft_score,
                "omw": round(enrollment.draft_omw, 2),
                "pgw": round(enrollment.draft_pgw, 2),
                "ogw": round(enrollment.draft_ogw, 2),
            }
            for enrollment in sorted_players
        ]

        return standings_out

    return get_or_set_cache(cache_key, fetch_draft_standings, timeout=None)


def tournament_standings(tournament):
    """Returns the current round's standings for the given tournament."""
    cache_key = f"tournament_standings_{tournament.id}_{tournament.current_round}"
    print("cache_key", cache_key)

    def fetch_tournament_standings():
        if tournament.current_round <= 1:
            return None

        players = enrollments_for_tournament(tournament)
        sorted_players = sorted(
            players,
            key=lambda x: (x.score, x.omw, x.pgw, x.ogw, x.player.user.name),
            reverse=True,
        )

        standings_out = [
            {
                "name": enrollment.player.user.name,
                "score": enrollment.score,
                "omw": round(enrollment.omw, 2),
                "pgw": round(enrollment.pgw, 2),
                "ogw": round(enrollment.ogw, 2),
            }
            for enrollment in sorted_players
        ]

        return standings_out

    return get_or_set_cache(cache_key, fetch_tournament_standings, timeout=None)


def reset_cache(tournament):
    """Resets the cache for the given tournament."""
    cache.clear()


def active_phase(tournament, force_update=False):
    """Returns the active phase for the given tournament."""
    cache_key = f"active_phase_{tournament.id}"

    def fetch_active_phase():
        try:
            return Phase.objects.get(
                tournament=tournament, started=True, finished=False
            )
        except Phase.DoesNotExist:
            return None

    return get_or_set_cache(cache_key, fetch_active_phase, 30, force_update)


def get_phase_by_index(tournament, index, force_update=False):
    """Returns the phase with the given index for the given tournament."""
    cache_key = f"phase_by_index_{tournament.id}_{index}"

    def fetch_phase_by_index():
        try:
            return Phase.objects.get(tournament=tournament, phase_idx=index)
        except Phase.DoesNotExist:
            return None

    return get_or_set_cache(cache_key, fetch_phase_by_index, None, force_update)


def player_records(tournament):
    players = enrollments_for_tournament(tournament, force_update=True)

    if not players:
        return None
    for enrollment in players:
        # print(f'Player {enrollment.player}:')
        games = enrollment_match_history(enrollment, tournament, force_update=True)
        player_record = {}
        drafts = Draft.objects.filter(Q(enrollments=enrollment))

        for d in drafts:
            player_record[d.slug] = {1: "", 2: "", 3: ""}
        for g in games:
            draft = g.round.draft
            player_role = 1
            if g.player2 == enrollment:
                player_role = 2
            p_wins = g.player1_wins if player_role == 1 else g.player2_wins
            op_wins = g.player2_wins if player_role == 1 else g.player1_wins
            outcome = 1 if p_wins > op_wins else -1 if p_wins < op_wins else 0
            player_record[draft.slug][g.round.round_idx] = outcome
