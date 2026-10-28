"""Small, deterministic synthetic insight dataset for the fan-facing demo."""
from __future__ import annotations

import math
import random

MODEL_VERSION = "matchsense-synthetic-xg-v1"
PRESSURE_VERSION = "observed-pressure-outcomes-v1"
TACTICS_VERSION = "synthetic-shape-observations-v1"
PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0

TEAMS = {
    "blue": {"name": "Club del Faro", "color": "#39a978"},
    "amber": {"name": "Puerto Lumbre FC", "color": "#efa94a"},
}

ROSTER = [
    ("01", "Iker Sol", "keeper", "GK"),
    ("02", "Nico Arce", "defender", "DF"),
    ("03", "Leo Mar", "defender", "DF"),
    ("04", "Gael Cruz", "defender", "DF"),
    ("05", "Iván Paz", "defender", "DF"),
    ("06", "Milo Rey", "midfielder", "MF"),
    ("08", "Dani Luna", "midfielder", "MF"),
    ("10", "Teo Ríos", "midfielder", "MF"),
    ("07", "Beni Vidal", "forward", "FW"),
    ("09", "Santi Sol", "forward", "FW"),
    ("11", "Ari León", "forward", "FW"),
]


def _sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def _shot_xg(shot: dict) -> tuple[float, float, float]:
    """Versioned, interpretable demo model; not trained on real match data."""
    attack_x = shot["x_m"] if shot["team_id"] == "blue" else PITCH_LENGTH_M - shot["x_m"]
    y = shot["y_m"] if shot["team_id"] == "blue" else PITCH_WIDTH_M - shot["y_m"]
    goal_x = PITCH_LENGTH_M
    distance = math.hypot(goal_x - attack_x, 34 - y)
    post_top = math.atan2(34 + 3.66 - y, goal_x - attack_x)
    post_bottom = math.atan2(34 - 3.66 - y, goal_x - attack_x)
    angle = abs(math.degrees(post_top - post_bottom))
    # A small, explicit synthetic formula keeps the demo inspectable. The
    # probabilities are illustrative and are not a real-football xG model.
    log_odds = (
        -1.55
        + (16 - distance) * 0.085
        + (angle - 30) * 0.028
        - (0.65 if shot["body_part"] == "head" else 0)
        - 0.28 * min(shot["defenders_nearby"], 3)
        + (1.35 if shot["play_type"] == "penalty" else 0)
        + (0.18 if shot["play_type"] == "counter" else 0)
        + (0.2 if shot["keeper_out_of_position"] else 0)
    )
    return round(max(0.01, min(0.95, _sigmoid(log_odds))), 3), round(distance, 1), round(angle, 1)


def _shots() -> list[dict]:
    profiles = [
        ("home_09", 98, 34, "foot", "open_play", 0, False),
        ("home_09", 92, 29, "foot", "counter", 1, False),
        ("home_11", 89, 40, "head", "cross", 2, False),
        ("home_08", 82, 34, "foot", "open_play", 1, True),
        ("home_07", 76, 22, "foot", "open_play", 2, False),
        ("home_10", 70, 47, "foot", "open_play", 0, False),
        ("away_09", 7, 34, "foot", "open_play", 0, False),
        ("away_09", 13, 39, "foot", "counter", 1, True),
        ("away_11", 16, 28, "head", "cross", 1, False),
        ("away_08", 23, 34, "foot", "open_play", 2, False),
        ("away_07", 29, 46, "foot", "open_play", 1, False),
        ("away_10", 35, 21, "foot", "penalty", 0, False),
    ]
    rng = random.Random(20261027)
    shots = []
    for index, (player_id, x, y, body, play_type, defenders, keeper_out) in enumerate(profiles, 1):
        team_id = "blue" if player_id.startswith("home") else "amber"
        world_y = y if team_id == "blue" else PITCH_WIDTH_M - y
        shot = {
            "id": f"shot-{index:02d}",
            "team_id": team_id,
            "team_name": TEAMS[team_id]["name"],
            "player_id": player_id,
            "player_name": next(row[1] for row in ROSTER if f"{'home' if team_id == 'blue' else 'away'}_{row[0]}" == player_id),
            "x_m": float(x),
            "y_m": float(world_y),
            "body_part": body,
            "play_type": play_type,
            "defenders_nearby": defenders,
            "keeper_out_of_position": keeper_out,
        }
        shot["xg"], shot["distance_m"], shot["angle_deg"] = _shot_xg(shot)
        shot["goal"] = rng.random() < shot["xg"]
        shot["outcome"] = "goal" if shot["goal"] else "saved_or_missed"
        shots.append(shot)
    return shots


def _pressure_episodes() -> list[dict]:
    outcomes = (
        ["pressing_team_regained"] * 5
        + ["pressed_team_kept_and_progressed"] * 4
        + ["pressed_team_kept_no_clear_progress"] * 3
        + ["incomplete"] * 2
    )
    episodes = []
    for index, outcome in enumerate(outcomes, 1):
        pressured_team = "blue" if index % 2 else "amber"
        pressing_team = "amber" if pressured_team == "blue" else "blue"
        recovery_id = f"{'home' if pressing_team == 'blue' else 'away'}_08" if outcome == "pressing_team_regained" else None
        episodes.append({
            "id": f"pressure-{index:02d}",
            "time_s": 14 + index * 4,
            "pressing_team_id": pressing_team,
            "pressing_team": TEAMS[pressing_team]["name"],
            "pressured_team_id": pressured_team,
            "pressured_team": TEAMS[pressured_team]["name"],
            "nearby_defenders": 1 + index % 3,
            "distance_m": round(1.2 + (index % 5) * 0.45, 1),
            "outcome": outcome,
            "recovery_player_id": recovery_id,
            "window_s": 5,
        })
    return episodes


def _tactical_scenario(scenario_id: str) -> dict:
    high_press = scenario_id == "high-press"
    line_bases = {"defender": 34.0, "midfielder": 53.0, "forward": 72.0} if high_press else {
        "defender": 25.0, "midfielder": 39.0, "forward": 51.0
    }
    carrier_x = [84, 82, 80, 78, 76, 74] if high_press else [72, 68, 64, 60, 56, 54]
    rows = {
        "defender": [10, 24, 44, 58],
        "midfielder": [15, 34, 53],
        "forward": [21, 47, 34],
    }
    role_numbers = {"defender": ["02", "03", "04", "05"], "midfielder": ["06", "08", "10"], "forward": ["07", "09", "11"]}
    frames = []
    for second, ball_x in enumerate(carrier_x):
        home_players = [{"player_id": "home_01", "team_id": "blue", "role": "keeper", "x_m": 7.0, "y_m": 34.0}]
        for role, numbers in role_numbers.items():
            for index, (number, y) in enumerate(zip(numbers, rows[role])):
                if high_press and role == "forward":
                    movement = second * 2.5
                elif not high_press and role == "midfielder" and number == "08":
                    movement = second * 3.8
                else:
                    movement = second * 0.35
                x = line_bases[role] + movement + (index - 1) * 0.6
                home_players.append({"player_id": f"home_{number}", "team_id": "blue", "role": role, "x_m": round(x, 1), "y_m": float(y)})
        away_players = [{"player_id": "away_01", "team_id": "amber", "role": "keeper", "x_m": 98.0, "y_m": 34.0}]
        for role, numbers, xs, ys in [
            ("defender", ["02", "03", "04", "05"], [68, 70, 70, 68], [10, 24, 44, 58]),
            ("midfielder", ["06", "08", "10"], [55, 57, 55], [15, 34, 53]),
            ("forward", ["07", "09", "11"], [44, 47, 44], [21, 34, 47]),
        ]:
            for number, x, y in zip(numbers, xs, ys):
                if number == "08":
                    x, y = ball_x, 34.0
                away_players.append({"player_id": f"away_{number}", "team_id": "amber", "role": role, "x_m": float(x), "y_m": float(y)})
        frames.append({"second": second, "ball": {"x_m": float(ball_x), "y_m": 34.0}, "players": home_players + away_players})

    run = 0
    trigger_frame = None
    for frame in frames:
        carrier = next(p for p in frame["players"] if p["player_id"] == "away_08")
        pressers = [p for p in frame["players"] if p["team_id"] == "blue" and p["role"] != "keeper"]
        nearest = min(math.hypot(p["x_m"] - carrier["x_m"], p["y_m"] - carrier["y_m"]) for p in pressers)
        run = run + 1 if nearest <= 4 else 0
        if run >= 2:
            trigger_frame = frame
            break
    trigger_observed = trigger_frame is not None
    trigger_frame = trigger_frame or frames[-1]
    home = [p for p in trigger_frame["players"] if p["team_id"] == "blue" and p["role"] != "keeper"]
    line_means = {role: round(sum(p["x_m"] for p in home if p["role"] == role) / len([p for p in home if p["role"] == role]), 1) for role in ("defender", "midfielder", "forward")}
    ball_x = trigger_frame["ball"]["x_m"]
    zone = "attacking third" if ball_x >= 70 else "middle third" if ball_x >= 35 else "defensive third"
    return {
        "id": scenario_id,
        "label": "High press" if high_press else "Mid-block",
        "description": "Authored synthetic tactic; plotted positions are generated observations.",
        "trigger_time_s": trigger_frame["second"],
        "trigger_observed": trigger_observed,
        "trigger_x_m": ball_x,
        "trigger_zone": zone,
        "team_length_m": round(max(p["x_m"] for p in home) - min(p["x_m"] for p in home), 1),
        "team_width_m": round(max(p["y_m"] for p in home) - min(p["y_m"] for p in home), 1),
        "line_heights_m": line_means,
        "line_gaps_m": {
            "defense_midfield": round(abs(line_means["midfielder"] - line_means["defender"]), 1),
            "midfield_forward": round(abs(line_means["forward"] - line_means["midfielder"]), 1),
        },
        "frame": trigger_frame,
    }


def build_demo_insights() -> dict:
    """Return reproducible synthetic metrics for a local, user-testable page."""
    shots = _shots()
    pressure = _pressure_episodes()
    known = [episode for episode in pressure if episode["outcome"] != "incomplete"]
    regains = [episode for episode in known if episode["outcome"] == "pressing_team_regained"]
    outcomes = {
        "pressing_team_regained": len(regains),
        "pressed_team_kept_and_progressed": sum(e["outcome"] == "pressed_team_kept_and_progressed" for e in known),
        "pressed_team_kept_no_clear_progress": sum(e["outcome"] == "pressed_team_kept_no_clear_progress" for e in known),
        "incomplete": len(pressure) - len(known),
    }

    # This compact ledger powers the role cards; it intentionally has no
    # cross-role score or ranking.
    passes = [
        {"player_id": "home_08", "team_id": "blue", "forward_m": d, "completed": c}
        for d, c in [(11, True), (14, True), (8, True), (4, True), (17, False), (9, True), (13, True), (6, False)]
    ] + [
        {"player_id": "home_04", "team_id": "blue", "forward_m": d, "completed": c}
        for d, c in [(7, True), (5, True), (6, True), (12, True), (8, False)]
    ] + [
        {"player_id": "away_06", "team_id": "amber", "forward_m": d, "completed": c}
        for d, c in [(10, True), (7, True), (14, True), (5, False), (9, True), (6, True)]
    ]
    recoveries = {}
    for episode in regains:
        player_id = episode["recovery_player_id"]
        recoveries[player_id] = recoveries.get(player_id, 0) + 1
    player_lookup = {f"{prefix}_{number}": {"number": number, "name": name, "role": role, "role_code": code, "team_id": team_id} for prefix, team_id in [("home", "blue"), ("away", "amber")] for number, name, role, code in ROSTER}
    active_players = {shot["player_id"] for shot in shots}
    active_players.update(row["player_id"] for row in passes)
    active_players.update(recoveries)
    ordered_players = [f"{prefix}_{number}" for prefix in ("home", "away") for number, *_ in ROSTER if f"{prefix}_{number}" in active_players]
    contributions = []
    for player_id in ordered_players:
        profile = player_lookup[player_id]
        player_shots = [shot for shot in shots if shot["player_id"] == player_id]
        player_passes = [row for row in passes if row["player_id"] == player_id]
        contributions.append({
            "player_id": player_id,
            **profile,
            "team_name": TEAMS[profile["team_id"]]["name"],
            "progressive_passes_completed": sum(p["completed"] and p["forward_m"] >= 5 for p in player_passes),
            "progressive_passes_attempted": sum(p["forward_m"] >= 5 for p in player_passes),
            "recoveries": recoveries.get(player_id, 0),
            "shots": len(player_shots),
            "xg": round(sum(s["xg"] for s in player_shots), 3),
        })

    return {
        "source": "fictional synthetic replay",
        "teams": TEAMS,
        "versions": {"xg": MODEL_VERSION, "pressure": PRESSURE_VERSION, "tactics": TACTICS_VERSION},
        "xg": {
            "model_version": MODEL_VERSION,
            "model_note": "Demo estimate calculated from shot location, angle, body part, play type, nearby defenders and goalkeeper position.",
            "explanation": "A shot's xG estimates its goal probability. 0.20 means around 2 goals per 10 similar chances on average; it is not a promise for this shot.",
            "shots": shots,
            "teams": [
                {"team_id": team_id, "team_name": TEAMS[team_id]["name"], "xg": round(sum(s["xg"] for s in shots if s["team_id"] == team_id), 2), "goals": sum(s["goal"] for s in shots if s["team_id"] == team_id), "shots": sum(s["team_id"] == team_id for s in shots)}
                for team_id in TEAMS
            ],
        },
        "pressure": {
            "definition_version": PRESSURE_VERSION,
            "definition": "Episode begins when generated tracking shows a defender within 4 m of the ball carrier for consecutive frames; outcome is observed over the next 5 s.",
            "episodes": pressure,
            "summary": {"total": len(pressure), "known": len(known), "incomplete": len(pressure) - len(known), "regains": len(regains), "regain_rate": round(len(regains) / len(known), 3) if known else None, "outcomes": outcomes},
        },
        "tactics": {"definition_version": TACTICS_VERSION, "scenarios": [_tactical_scenario("high-press"), _tactical_scenario("mid-block")]},
        "players": contributions,
        "limits": [
            "All scenes and values on this page are synthetic demonstrations, not real match or league statistics.",
            "The xG formula is educational and uncalibrated against real shots.",
            "Pressure outcomes are temporal observations, not proof that pressure caused a turnover.",
            "Tactical labels are authored scenario metadata; line geometry is computed from the displayed positions.",
            "Player cards show event contributions, not ratings or rankings.",
        ],
    }
