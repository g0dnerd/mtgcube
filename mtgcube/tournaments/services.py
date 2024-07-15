import random

from .models import Game, Enrollment, Draft, Round


def pair_current_round(draft: Draft):
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

    print("Pairing players...")

    players = list(Enrollment.objects.filter(draft=draft))

    random.shuffle(players)

    draft.phase.current_round += 1
    draft.phase.save()

    for player in players:
        player.paired = False

    sorted_players = sorted(
        players, key=lambda x: (x.score, x.omw, x.pgw, x.ogw), reverse=True
    )
    pairings = []

    # Assign a bye if necessary
    """ if len(sorted_players) % 2 == 1:
        for player in reversed(sorted_players):
            if not player.had_bye:
                print("Assigning bye to", player.name)
                pairings.append((player, None))
                player.had_bye = True """
    # TODO: Add a result

    # Pair players
    for player in sorted_players:
        if not player.paired:
            for opponent in sorted_players:
                if opponent != player:
                    if not opponent.paired:
                        if opponent not in player.pairings.all():
                            pairings.append((player, opponent))
                            pair(draft, player, opponent, len(pairings))
                            break

    for table, pairing in enumerate(pairings):
        print(f"Table {table + 1}: {pairing[0]} vs {pairing[1]}")


def pair(draft, player1, player2, table):
    round = Round.objects.filter(draft=draft).order_by("-round_idx").first()
    game = Game(
        round=round,
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


def update_result(game_id, player1_wins, player2_wins):
    game = Game.objects.get(pk=game_id)
    game.player1_wins = player1_wins
    game.player2_wins = player2_wins
    game.player1.games_won += player1_wins
    game.player2.games_won += player2_wins
    game.player1.games_played += player1_wins + player2_wins
    game.player2.games_played += player1_wins + player2_wins
    game.save()
    if player1_wins > player2_wins:
        game.player1.score += 3
    elif player2_wins > player1_wins:
        game.player2.score += 3
    else:
        game.player1.score += 1
        game.player2.score += 1
    game.player1.save()
    game.player2.save()


def update_tiebreakers(draft):
    players = draft.enrollments.all()
    round_num = Round.objects.filter(draft=draft).order_by("-round_idx").first().round_idx
    for player in players:
        player.pmw = max(round((player.score // 3) / round_num, 2), 0.33)
        player.omw = 0
        player.pgw = max(round(player.games_won / player.games_played, 2), 0.33)
        player.ogw = 0
        player.save()
    for player in players:
        for opponent in player.pairings.all():
            player.omw += opponent.pmw
            player.ogw += opponent.pgw
        player.omw = max(round(player.omw / round_num, 2), 0.33)
        player.ogw = max(round(player.ogw / round_num, 2), 0.33)
        player.save()

def finish_round(draft: Draft):
    current_round = Round.objects.filter(draft=draft).order_by("-round_idx").first()
    current_round.finished = True
    if current_round.round_idx < draft.round_number:
        new_round = Round(
            draft = draft,
            round_idx = current_round.round_idx + 1
        )
        new_round.save()

def standings(draft, update=True):
    if update:
        update_tiebreakers(draft)
    players = draft.enrollments.all()
    sorted_players = sorted(
        players, key=lambda x: (x.score, x.omw, x.pgw, x.ogw), reverse=True
    )
    return sorted_players

def seatings(draft):
    players = list(draft.enrollments.all())
    random.shuffle(players)
    for idx, player in enumerate(players):
        player.seat = idx + 1
        player.save()
    draft.seated = True
    draft.save()

def clear_histories(draft):
    draft.seated = False
    draft.save()

    draft.phase.current_round = 0
    draft.phase.save()
    
    players = draft.enrollments.all()

    try:
        rounds = Round.objects.filter(draft=draft)
    except Round.DoesNotExist as exc:
        raise ValueError("Could not find any rounds to reset") from exc
    
    for round in rounds:
        round.started = False
        round.finished = False
        round.save()

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
        player.pairings.clear()
        player.paired = False
        player.had_bye = False
        player.save()
