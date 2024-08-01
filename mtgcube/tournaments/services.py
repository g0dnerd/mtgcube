import random

from .models import Game, Enrollment, Round
from . import queries


def seat_draft(draft):
    reset_draft_scores(draft)
    players = list(draft.enrollments.all())

    random.shuffle(players)
    for idx, player in enumerate(players):
        player.seat = idx + 1
    draft.seated = True
    draft.started = True
    draft.save()


def pair_round(draft):
    """
    Definition of Swiss Pairing:
    1. For the first round, players are paired randomly (or fixed by the tournament organizer).
    2. For each subsequent round, the highest-ranked player is paired with the next highest-ranked player they have not yet played.
    3. The highest-ranked player among the remaining players is paired with the next highest-ranked player they have not yet played and so on.
    4. If there is an odd number of players, the lowest-ranked player who has not yet had a bye is given a bye.
    5. When ranking players, the order of tiebreakers is as follows:
        Opponent's Match Win Percentage (OMW)
        Player Game Win Percentage (PGW)
        Opponent Game Win Percentage (OGW)
        Note: Tiebreakers that are below .33 are set to .33 instead.
        Byes are NOT included when calculating tiebreakers.
    PROCESS:
    1. Sort players by points and tiebreakers
    2. Pair players in the sorted list
    3. If a pairing is not possible because the players have already played each other, pair each player with
        the next player down they have not already played.
    4. If there is an odd number of players, give a bye to the lowest ranked player who has not already had a bye.
    """

    current_round = queries.current_round(draft, force_update=True)

    if current_round:
        if current_round.round_idx == draft.round_number:
            return IndexError("Draft already has all rounds.")
        new_rd = Round(draft=draft, round_idx=current_round.round_idx + 1)
        new_rd.save()
    else:
        new_rd = Round(draft=draft, round_idx=1)
        new_rd.save()

    players = list(Enrollment.objects.filter(draft=draft))

    random.shuffle(players)

    for player in players:
        player.paired = False
        player.bye_this_round = False
        player.save()

    sorted_players = sorted(
        players,
        key=lambda x: (x.draft_score, x.draft_omw, x.draft_pgw, x.draft_ogw),
        reverse=True,
    )
    pairings = []

    # Assign a bye if necessary
    if len(sorted_players) % 2 == 1:
        for player in reversed(sorted_players):
            if not player.had_bye:
                assign_bye(player)
                break

    # Pair players
    for player in sorted_players:
        if not player.paired:
            for opponent in sorted_players:
                if opponent != player:
                    if not opponent.paired:
                        if opponent not in player.pairings.all():
                            pairings.append((player, opponent))
                            pair(new_rd, player, opponent, len(pairings))
                            break

    new_rd.paired = True
    new_rd.save()


def assign_bye(player):
    player.paired = True
    player.had_bye = True
    player.bye_this_round = True
    player.draft_score += 3
    player.draft_games_played += 2
    player.draft_games_won += 2
    player.score += 3
    player.games_played += 2
    player.games_won += 2
    player.save()


def pair(rd: Round, player1, player2, table):
    game = Game(
        round=rd,
        player1=player1,
        player2=player2,
        table=table,
    )
    game.save()
    player1.paired = True
    player2.paired = True
    player1.pairings.add(player2)
    player2.pairings.add(player1)
    player1.save()
    player2.save()
    rd.paired = True
    rd.save()


def finish_match(match):
    match.result_confirmed = True
    match.save()

    p1 = match.player1
    p2 = match.player2
    p1_wins = match.player1_wins
    p2_wins = match.player2_wins
    p1.games_won += p1_wins
    p2.games_won += p2_wins
    p1.games_played += p1_wins + p2_wins
    p2.games_played += p1_wins + p2_wins
    p1.draft_games_won += p1_wins
    p2.draft_games_won += p2_wins
    p1.draft_games_played += p1_wins + p2_wins
    p2.draft_games_played += p1_wins + p2_wins

    if p1_wins > p2_wins:
        p1.score += 3
        p1.draft_score += 3
    elif p2_wins > p1_wins:
        p2.score += 3
        p2.draft_score += 3
    else:
        p1.score += 1
        p2.score += 1
        p1.draft_score += 1
        p2.draft_score += 1
    p1.save()
    p2.save()


def update_draft_tiebreakers(draft):
    players = draft.enrollments.all()
    current_round = queries.current_round(draft, force_update=True).round_idx

    for player in players:
        player.draft_pmw = max(
            round((player.draft_score // 3) / current_round, 2), 0.33
        )
        try:
            player.draft_pgw = max(
                round(player.draft_games_won / player.draft_games_played, 2), 0.33
            )
        except ZeroDivisionError:
            player.draft_pgw = 1.0
        player.draft_omw = 0.0
        player.draft_ogw = 0.0
        player.save()
    for player in players:
        for opponent in player.pairings.all():
            player.draft_omw += opponent.draft_pmw
            player.draft_ogw += opponent.draft_pgw
        player.draft_omw = max(round(player.draft_omw / current_round, 2), 0.33)
        player.draft_ogw = max(round(player.draft_ogw / current_round, 2), 0.33)
        player.save()


def update_tournament_tiebreakers(tournament):
    players = queries.enrollments_for_tournament(tournament, force_update=True)
    current_round = tournament.current_round

    for p in players:
        p.pmw = max(round((p.score // 3) / current_round, 2), 0.33)
        try:
            p.pgw = max(round(p.games_won / p.games_played, 2), 0.33)
        except ZeroDivisionError:
            p.pgw = 1.0
        p.omw = 0.0
        p.ogw = 0.0
        p.save()

    for p in players:
        matches = queries.enrollment_match_history(p, tournament)
        for m in matches:
            opp = m.player1 if m.player2 == p else m.player2
            p.omw += opp.pmw
            p.ogw += opp.pgw
        p.omw = max(round(p.omw / current_round, 2), 0.33)
        p.ogw = max(round(p.ogw / current_round, 2), 0.33)
        p.save()


def finish_draft_round(current_round: Round):
    current_round.finished = True
    current_round.save()

    draft = current_round.draft
    update_draft_tiebreakers(draft)

    players = draft.enrollments.all()

    # Update draft standings
    sorted_players = sorted(
        players,
        key=lambda x: (x.draft_score, x.draft_omw, x.draft_pgw, x.draft_ogw),
        reverse=True,
    )

    for idx, p in enumerate(sorted_players):
        p.draft_place = idx + 1
        p.save()


def finish_event_round(tournament):
    update_tournament_tiebreakers(tournament)
    players = queries.enrollments_for_tournament(tournament, force_update=True)

    tournament.current_round += 1
    tournament.save()

    # Update draft standings
    sorted_players = sorted(
        players,
        key=lambda x: (x.score, x.omw, x.pgw, x.ogw),
        reverse=True,
    )

    for idx, p in enumerate(sorted_players):
        p.place = idx + 1
        p.save()


def reset_draft_scores(draft):
    players = draft.enrollments.all()
    for player in players:
        player.draft_score = 0
        player.draft_games_played = 0
        player.draft_games_won = 0
        player.draft_omw = 0.0
        player.draft_pgw = 0.0
        player.draft_ogw = 0.0
        player.pairings.clear()
        player.had_bye = False
        player.save()


def clear_histories(draft):
    draft.seated = False
    draft.started = False
    draft.save()

    players = draft.enrollments.all()

    try:
        rounds = Round.objects.filter(draft=draft)
    except Round.DoesNotExist as exc:
        raise ValueError("Could not find any rounds to reset") from exc

    games = Game.objects.filter(round__in=rounds)
    for game in games:
        game.delete()
    for player in players:
        player.score = 0
        player.games_played = 0
        player.games_won = 0
        player.pmw = 0
        player.omw = 0
        player.pgw = 0
        player.ogw = 0
        player.draft_score = 0
        player.draft_games_played = 0
        player.draft_games_won = 0
        player.draft_pmw = 0
        player.draft_omw = 0
        player.draft_pgw = 0
        player.draft_ogw = 0
        player.place = 0
        player.draft_place = 0
        player.pairings.clear()
        player.paired = False
        player.had_bye = False
        player.bye_this_round = False
        player.save()

    for rd in rounds:
        rd.delete()
