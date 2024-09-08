import random

from django.utils import timezone
import networkx as nx

from .models import Game, Enrollment, Round, Draft, Phase
from . import queries


def seat_draft(draft):
    reset_draft_scores(draft)
    players = list(draft.enrollments.filter(dropped=False))

    random.shuffle(players)
    for idx, player in enumerate(players):
        player.seat = idx + 1
    draft.seated = True
    draft.started = True
    draft.save()


def pair_round_new(draft):
    current_round = queries.current_round(draft, force_update=True)

    if current_round:
        if current_round.round_idx == draft.round_number:
            return IndexError("Draft already has all rounds.")
        new_rd = Round(draft=draft, round_idx=current_round.round_idx + 1, started=True)
        new_rd.save()
    else:
        new_rd = Round(draft=draft, round_idx=1)
        new_rd.save()

    players = list(Enrollment.objects.filter(draft=draft, dropped=False))

    # Clear old round pairings
    for player in players:
        player.paired = False
        player.bye_this_round = False
        player.save()

    startingTable = draft.first_table

    openTable = startingTable

    # Contains lists of players sorted by how many points they currently have
    pointLists = {}

    # Contains a list of points in the event from high to low
    pointTotals = []

    # Counts our groupings for each point amount
    countPoints = {}

    # Add all players to pointLists
    for player in players:
        # If this point amount isn't in the list, add it
        if "%s_1" % player.draft_score not in pointLists:
            pointLists["%s_1" % player.draft_score] = []
            countPoints[player.draft_score] = 1

        # Breakers the players into groups of their current points up to the max group allowed.
        # Smaller groups mean faster calculations
        if (
            len(
                pointLists[
                    "%s_%s" % (player.draft_score, countPoints[player.draft_score])
                ]
            )
            > 25
        ):
            countPoints[player.draft_score] += 1
            pointLists[
                "%s_%s" % (player.draft_score, countPoints[player.draft_score])
            ] = []

        # Add our player to the correct group
        pointLists[
            "%s_%s" % (player.draft_score, countPoints[player.draft_score])
        ].append(player)

    # Add all points in use to pointTotals
    for points in pointLists:
        pointTotals.append(points)

    # Sort our point groups based on points
    pointTotals.sort(reverse=True, key=lambda s: int(s.split("_")[0]))

    print("Point totals after sorting high to low are: %s" % pointTotals, 3)

    # Actually pair the players utilizing graph theory networkx
    for points in pointTotals:
        print(points, 5)

        # Create the graph object and add all players to it
        bracketGraph = nx.Graph()
        bracketGraph.add_nodes_from(pointLists[points])

        print(pointLists[points], 5)
        print(bracketGraph.nodes(), 5)

        # Create edges between all players in the graph who haven't already played
        for player in bracketGraph.nodes():
            for opponent in bracketGraph.nodes():
                if opponent not in player.pairings.all() and player != opponent:
                    # Weight edges randomly between 1 and 9 to ensure pairings are not always the same with
                    # the same list of players
                    wgt = random.randint(1, 9)
                    # If a player has more points, weigh them the highest, so they get paired first
                    if player.draft_score > int(
                        points.split("_")[0]
                    ) or opponent.draft_score > int(points.split("_")[0]):
                        wgt = 10
                    # Create edge
                    bracketGraph.add_edge(player, opponent, weight=wgt)

        # Generate pairings from the created graph
        pairings = dict(nx.max_weight_matching(bracketGraph))

        print(pairings, 3)

        # Actually pair the players based on the matching we found
        for p in pairings:
            if p in pointLists[points]:
                pair(new_rd, p, pairings[p], openTable)
                openTable += 1
                pointLists[points].remove(p)
                pointLists[points].remove(pairings[p])

        print(pointLists[points], 5)

        # Check if we have an odd man out that we need to pair down
        if len(pointLists[points]) > 0:
            # Check to make sure we aren't at the last player in the event
            print(
                "Player %s left in %s. The index is %s and the length of totals is %s"
                % (
                    pointLists[points][0],
                    points,
                    pointTotals.index(points),
                    len(pointTotals),
                ),
                3,
            )
            if pointTotals.index(points) + 1 == len(pointTotals):
                while len(pointLists[points]) > 0:
                    # If they are the last player give them a bye
                    assign_bye(pointLists[points].pop(0))
            else:
                # Add our player to the next point group down
                nextPoints = pointTotals[pointTotals.index(points) + 1]

                while len(pointLists[points]) > 0:
                    pointLists[nextPoints].append(pointLists[points].pop(0))


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
            round((player.draft_score // 3) / current_round, 4), 0.33
        )
        try:
            player.draft_pgw = max(
                round(player.draft_games_won / player.draft_games_played, 4), 0.33
            )
        except ZeroDivisionError:
            player.draft_pgw = 1.0
        player.draft_omw = 0.0
        player.draft_ogw = 0.0
        player.save()
    for player in players:
        if len(player.pairings.all()) == 0:
            player.draft_omw = 1.0
            player.draft_ogw = 1.0
            player.save()
        else:
            for opponent in player.pairings.all():
                player.draft_omw += opponent.draft_pmw
                player.draft_ogw += opponent.draft_pgw
            player.draft_omw = max(round(player.draft_omw / current_round, 4), 0.33)
            player.draft_ogw = max(round(player.draft_ogw / current_round, 4), 0.33)
            player.save()


def update_tournament_tiebreakers(tournament):
    players = queries.enrollments_for_tournament(tournament, force_update=True)
    current_round = tournament.current_round

    for p in players:
        p.pmw = max(round((p.score // 3) / current_round, 4), 0.33)
        try:
            p.pgw = max(round(p.games_won / p.games_played, 4), 0.33)
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
        p.omw = max(round(p.omw / current_round, 4), 0.33)
        p.ogw = max(round(p.ogw / current_round, 4), 0.33)
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

    if current_round.round_idx == draft.round_number:
        draft.finished = True
        draft.save()


def finish_event_round(tournament):
    update_tournament_tiebreakers(tournament)

    players = queries.enrollments_for_tournament(tournament, force_update=True)

    phase = queries.active_phase(tournament, force_update=True)
    if tournament.current_round % phase.round_number == 0:
        phase.finished = True
        phase.save()

    tournament.current_round += 1
    tournament.save()
    print(f"Tournament is now in round {tournament.current_round}")

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
    for p in players:
        p.draft_score = 0
        p.draft_games_played = 0
        p.draft_games_won = 0
        p.draft_omw = 0.0
        p.draft_pgw = 0.0
        p.draft_ogw = 0.0
        p.pairings.clear()
        p.had_bye = False
        p.checked_in = False
        p.checked_out = False
        p.save()


def clear_histories(draft):
    draft.seated = False
    draft.started = False
    draft.finished = False
    draft.save()

    queries.reset_cache(draft.phase.tournament)

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
        checkin_images = queries.images(player.player.user, draft, checkin=True)
        for img in checkin_images:
            img.delete()
        checkout_images = queries.images(player.player.user, draft, checkin=False)
        for img in checkout_images:
            img.delete()
        player.checked_in = False
        player.checked_out = False
        player.save()

    for rd in rounds:
        rd.delete()


def reset_tournament(tournament):
    tournament.current_round = 1
    tournament.save()

    phases = Phase.objects.filter(tournament=tournament)
    drafts = Draft.objects.filter(phase__tournament=tournament)

    for p in phases:
        p.started = False
        p.finished = False
        p.save()

    for d in drafts:
        clear_histories(d)


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


def enroll_for_event(user, tournament):
    user_player = queries.get_player(user)

    if tournament.signed_up >= tournament.player_capacity:
        raise ValueError("Event is full.")

    enroll = queries.enrollment_from_tournament(tournament, user_player)
    if enroll:
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
            tournament=tournament, player=user_player, registration_finished=True
        )

    tournament.signed_up += 1
    tournament.save()
