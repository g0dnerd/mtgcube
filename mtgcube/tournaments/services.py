import random

from .models import Game, Enrollment, Round


def pair_round(rd: Round):
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

    draft = rd.draft

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
                assign_bye(rd, player)
                break

    # Pair players
    for player in sorted_players:
        if not player.paired:
            for opponent in sorted_players:
                if opponent != player:
                    if not opponent.paired:
                        if opponent not in player.pairings.all():
                            pairings.append((player, opponent))
                            pair(rd, player, opponent, len(pairings))
                            break

    rd.paired = True
    rd.save()


def assign_bye(rd: Round, player):
    player.had_bye = True
    player.paired = True
    player.bye_this_round = True
    player.draft_score += 3
    player.score += 3
    player.games_played += 2
    player.draft_games_played += 2
    player.games_won += 2
    player.draft_games_won += 2
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


def update_result(game, player1_wins, player2_wins):
    game.player1_wins = player1_wins
    game.player2_wins = player2_wins
    game.player1.games_won += player1_wins
    game.player2.games_won += player2_wins
    game.player1.games_played += player1_wins + player2_wins
    game.player2.games_played += player1_wins + player2_wins
    game.player1.draft_games_won += player1_wins
    game.player2.draft_games_won += player2_wins
    game.player1.draft_games_played += player1_wins + player2_wins
    game.player2.draft_games_played += player1_wins + player2_wins
    game.save()
    if player1_wins > player2_wins:
        game.player1.score += 3
        game.player1.draft_score += 3
    elif player2_wins > player1_wins:
        game.player2.score += 3
        game.player2.draft_score += 3
    else:
        game.player1.score += 1
        game.player2.score += 1
        game.player1.draft_score += 1
        game.player2.draft_score += 1
    game.player1.save()
    game.player2.save()


def sync_round(matches):
    for m in matches:
        update_result(m, m.player1_wins, m.player2_wins)


def update_tiebreakers(draft):
    players = draft.enrollments.all()
    round_num = (
        Round.objects.filter(draft=draft).order_by("-round_idx").first().round_idx
    )
    for player in players:
        player.pmw = max(round((player.score // 3) / round_num, 2), 0.33)
        player.draft_pmw = max(round((player.draft_score // 3) / round_num, 2), 0.33)
        try:
            player.pgw = max(round(player.games_won / player.games_played, 2), 0.33)
            player.draft_pgw = max(
                round(player.draft_games_won / player.draft_games_played, 2), 0.33
            )
        except ZeroDivisionError:
            player.pgw = 1.0
            player.draft_pmw = 1.0
            player.draft_pgw = 1.0
        player.omw = 0
        player.ogw = 0
        player.draft_omw = 0
        player.draft_ogw = 0
        player.save()
    for player in players:
        for opponent in player.pairings.all():
            player.omw += opponent.pmw
            player.ogw += opponent.pgw
            player.draft_omw += opponent.draft_pmw
            player.draft_ogw += opponent.draft_pgw
        player.omw = max(round(player.omw / round_num, 2), 0.33)
        player.ogw = max(round(player.ogw / round_num, 2), 0.33)
        player.draft_omw = max(round(player.draft_omw / round_num, 2), 0.33)
        player.draft_ogw = max(round(player.draft_ogw / round_num, 2), 0.33)
        player.paired = False
        player.save()


def reset_draft_scores(draft):
    players = draft.enrollments.all()
    for player in players:
        player.draft_score = 0
        player.draft_games_played = 0
        player.draft_games_won = 0
        player.draft_omw = 0.0
        player.draft_pgw = 0.0
        player.draft_ogw = 0.0
        player.paired = False
        player.pairings.clear()
        player.had_bye = False
        player.save()


def draft_standings(draft, update=True):
    if update:
        update_tiebreakers(draft)
    players = draft.enrollments.all()
    sorted_players = sorted(
        players,
        key=lambda x: (x.draft_score, x.draft_omw, x.draft_pgw, x.draft_ogw),
        reverse=True,
    )
    return sorted_players


def event_standings(tournament):
    players = Enrollment.objects.filter(tournament=tournament).all()
    sorted_players = sorted(
        players, key=lambda x: (x.score, x.omw, x.pgw, x.ogw), reverse=True
    )
    return sorted_players


def seatings(draft):
    players = list(draft.enrollments.all())

    random.shuffle(players)
    for idx, player in enumerate(players):
        player.seat = idx + 1
        player.draft_score = 0
        player.draft_games_played = 0
        player.draft_games_won = 0
        player.draft_pmw = 0
        player.draft_omw = 0
        player.draft_pgw = 0
        player.draft_ogw = 0
        player.pairings.clear()
        player.paired = False
        player.had_bye = False
        player.save()
    draft.seated = True
    draft.started = True
    draft.save()

    new_round = Round(
        draft=draft,
        round_idx=1,
        finished=False,
        started=False,
        paired=False,
    )
    new_round.save()


def clear_histories(draft):
    draft.seated = False
    draft.started = False
    draft.save()

    draft.phase.current_round = 0
    draft.phase.save()

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
        player.pairings.clear()
        player.paired = False
        player.had_bye = False
        player.bye_this_round = False
        player.save()

    for rd in rounds:
        rd.delete()
