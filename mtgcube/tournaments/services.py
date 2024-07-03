import random

from .models import Tournament, Game, Player, Enrollment

def pair_current_round(tournament):
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
    
    players = list(Enrollment.objects.filter(tournament=tournament.id))
    
    random.shuffle(players)

    tournament.current_round += 1
    print("Updated current round to", tournament.current_round)
    try:
        tournament.save()
    except:
        print("Error saving tournament")

    for player in players:
        player.paired = False

    sorted_players = sorted(players, key=lambda x: (x.score, x.omw, x.pgw, x.ogw), reverse=True)
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
                            pair(tournament, player, opponent, len(pairings))
                            break

    for table, pairing in enumerate(pairings):
        print(f"Table {table + 1}: {pairing[0]} vs {pairing[1]}")


def pair(tournament, player1, player2, table):
    game = Game(tournament=tournament, player1=player1, player2=player2, table=table, round=tournament.current_round)
    game.save()
    player1.paired = True
    player2.paired = True
    player1.pairings.add(player2)
    player2.pairings.add(player1)
    player1.save()
    player2.save()

def report_result(game_id, player1_wins, player2_wins):
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

def update_tiebreakers(tournament):
    players = Enrollment.objects.filter(tournament=tournament.id)
    for player in players:
        player.pmw = max(round((player.score//3)/len(player.played.all()),2),0.33)
        player.omw = 0
        player.pgw = max(round(player.games_won/player.games_played,2),0.33)
        player.ogw = 0
        player.save()
    for player in players:
        for opponent in player.pairings.all():
            player.omw += opponent.pmw
            player.ogw += opponent.pgw
        player.omw = max(round(player.omw/len(player.played.all()),2),0.33)
        player.ogw = max(round(player.ogw/len(player.played.all()),2),0.33)
        player.save()

def make_standings(tournament):
    players = Enrollment.objects.filter(tournament=tournament.id)
    sorted_players = sorted(players, key=lambda x: (x.score, x.omw, x.pgw, x.ogw), reverse=True)
    return sorted_players

def clear_histories(tournament_id):
    tournament = Tournament.objects.get(pk=tournament_id)
    tournament.current_round = 0
    tournament.save()
    players = Enrollment.objects.filter(tournament=tournament_id)
    games = Game.objects.filter(tournament=tournament_id)
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