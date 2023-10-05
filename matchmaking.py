import random
from dataclasses import dataclass
from itertools import product
from time import time
from typing import Dict, Generator, List, Set, Tuple


@dataclass(frozen=True)
class PlayerRoleMMR:
    player_id: str
    role: str
    mmr: int
    primary_role: bool
    num_games_played: int


Players = Set[PlayerRoleMMR]

valid_roles = ["carry", "support", "mid", "jg", "solo"]


def create_dummy_data(n: int) -> Players:
    data = []
    for i in range(n):
        roles = random.sample(valid_roles, k=3)
        primary_role = [True, False, False]
        random.shuffle(primary_role)
        for role, primary in zip(roles, primary_role):
            data.append(
                PlayerRoleMMR(
                    player_id=str(i),
                    role=role,
                    mmr=random.randint(1200, 1800),
                    primary_role=primary,
                )
            )
    return data


Team = Set[PlayerRoleMMR]
Match = Tuple[Team, Team]
Matches = List[Match]


def match_quality(match: Match) -> int:
    overall_mmr = abs(sum((x.mmr for x in match[0])) - sum((x.mmr for x in match[1])))
    by_role_mmr = 0
    for role in valid_roles:
        match_0_role = [x for x in match[0] if x.role == role][0]
        match_1_role = [x for x in match[1] if x.role == role][0]
        by_role_mmr += abs(match_0_role.mmr - match_1_role.mmr)
    players_on_primary_role = [x for x in match[0] if x.primary_role] + [
        x for x in match[1] if x.primary_role
    ]
    return ((overall_mmr * 0.4) + (by_role_mmr * 0.6)) * (
        1.0 - (0.04 * len(players_on_primary_role))
    )


def match_avg_mmr_diff(match: Match) -> Tuple[float, float]:
    overall_mmr = abs(sum((x.mmr for x in match[0])) - sum((x.mmr for x in match[1])))
    by_role_mmr = 0
    for role in valid_roles:
        match_0_role = [x for x in match[0] if x.role == role][0]
        match_1_role = [x for x in match[1] if x.role == role][0]
        by_role_mmr += abs(match_0_role.mmr - match_1_role.mmr)

    return overall_mmr / 10, by_role_mmr / 5


def build_teams(
    players_by_role: Dict[str, PlayerRoleMMR],
    team: Team,
) -> Generator[Team, None, None]:
    potential_teams = product(*players_by_role.values())
    for team in potential_teams:
        if len({x.player_id for x in team}) == len(valid_roles):
            yield set(team)


def build_matchups(
    all_teams: Generator[Team, None, None]
) -> Generator[Match, None, None]:
    for t1 in all_teams:
        for t2 in all_teams:
            player_id_t1 = {x.player_id for x in t1}
            player_id_t2 = {x.player_id for x in t2}
            if len(player_id_t1.intersection(player_id_t2)) > 0:
                continue
            else:
                yield t1, t2


def matchmake(all_players: Players) -> Matches:
    matchups: Matches = []
    while True:  # exit via 'break' when no more matches can be created
        print("Sorting players by MMR")
        sorted_by_mmr = sorted(all_players, key=lambda x: x.mmr, reverse=True)

        print("Grouping players by role")
        role_sets = {}
        for player in sorted_by_mmr:
            if player.role not in role_sets:
                role_sets[player.role] = []
            role_sets[player.role].append(player)

        top_5_in_each_role = []
        for players in role_sets.values():
            top_5_in_each_role += players[:5]

        possible_teams = build_teams(players_by_role=role_sets, team=set())
        possible_matchups = build_matchups(possible_teams)

        print("Calculating best matchup")
        try:
            best_matchup = min(possible_matchups, key=match_quality)
        except ValueError:
            print("all possible matches created")
            break

        print(f"Best matchup: {best_matchup}\nScore: {match_quality(best_matchup)}")

        removed_players = [x.player_id for x in best_matchup[0]] + [
            x.player_id for x in best_matchup[1]
        ]
        print(f"Removing players: {removed_players}")

        all_players = {
            x
            for x in all_players
            if x.player_id not in {y.player_id for y in best_matchup[0]}
            and x.player_id not in {z.player_id for z in best_matchup[1]}
        }

        print(f"Remaining players: { {x.player_id for x in all_players} }")

        matchups.append(best_matchup)

    return matchups


if __name__ == "__main__":
    for num_players in [30, 40]:
        start = time()
        matchmake(create_dummy_data(num_players))
        end = time()
        print(f"{num_players} players: {end - start}")
