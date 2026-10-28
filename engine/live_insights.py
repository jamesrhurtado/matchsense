"""Match-clock scoped fan metrics derived from the delivered synthetic feed."""
from __future__ import annotations

import math

from engine.core import available
from engine.match_state import latest_events

XG_VERSION = "matchsense-shot-context-xg-illustrative-v1"
PROGRESSIVE_PASS_M = 5.0
PRESSURE_RADIUS_M = 4.0
PRESSURE_OUTCOME_MS = 5000
PRESSURE_PROGRESS_M = 5.0
MAX_TRACKING_GAP_MS = 200
PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0
GOAL_HALF_WIDTH_M = 3.66


def _rank(message: dict) -> tuple:
    return (message["revision"], message["sequence_no"], message["message_id"])


def _frames_at(messages: list[dict]) -> list[dict]:
    by_time: dict[int, dict] = {}
    for message in messages:
        if message["kind"] != "tracking_frame":
            continue
        old = by_time.get(message["timeline_ms"])
        if old is None or _rank(message) > _rank(old):
            by_time[message["timeline_ms"]] = message
    return [by_time[key] for key in sorted(by_time)]


def _frame_before(frames: list[dict], at_ms: int) -> dict | None:
    candidates = [frame for frame in frames if frame["timeline_ms"] <= at_ms]
    return candidates[-1] if candidates else None


def _period_direction(meta: dict, period_number: int, team_id: str) -> int:
    period = next(
        (row for row in meta["periods"] if row["period"] == period_number),
        meta["periods"][0],
    )
    return 1 if period["attack_direction"].get(team_id) == "right" else -1


def _distance(a: dict, b: dict) -> float:
    return math.hypot(a["x_m"] - b["x_m"], a["y_m"] - b["y_m"])


def _xg_estimate(
    meta: dict,
    frames: list[dict],
    start: dict,
    team_id: str,
) -> dict:
    details = start["payload"]["details"]
    location = details.get("location")
    body_part = details.get("body_part")
    play_type = details.get("play_type")
    unavailable = {
        "xg": None,
        "distance_m": None,
        "angle_deg": None,
        "nearby_defenders": None,
        "body_part": body_part,
        "play_type": play_type,
        "reason": "Shot location, shot context or nearby tracking is unavailable.",
    }
    if not location or body_part not in {"foot", "head"} or play_type not in {"open_play", "counter", "set_piece", "penalty"}:
        return unavailable
    frame = _frame_before(frames, start["timeline_ms"])
    if not frame or start["timeline_ms"] - frame["timeline_ms"] > MAX_TRACKING_GAP_MS:
        return unavailable

    team_ids = {team["id"] for team in meta["teams"]}
    defending_team = next((candidate for candidate in team_ids if candidate != team_id), None)
    if defending_team is None:
        return unavailable
    expected_defenders = {
        player["id"]
        for player in meta["players"]
        if player["team_id"] == defending_team and player.get("role") != "keeper"
    }
    observed = {
        player["player_id"]: player
        for player in frame["payload"].get("players", [])
    }
    if not expected_defenders.issubset(observed):
        return unavailable

    point = {"x_m": location["x_m"], "y_m": location["y_m"]}
    defenders_nearby = sum(
        _distance(point, observed[player_id]) <= PRESSURE_RADIUS_M
        for player_id in expected_defenders
    )
    attack_right = _period_direction(meta, start["period"], team_id) > 0
    goal_x = PITCH_LENGTH_M if attack_right else 0.0
    distance_m = math.hypot(goal_x - point["x_m"], PITCH_WIDTH_M / 2 - point["y_m"])
    angle_top = math.atan2(
        PITCH_WIDTH_M / 2 + GOAL_HALF_WIDTH_M - point["y_m"],
        goal_x - point["x_m"],
    )
    angle_bottom = math.atan2(
        PITCH_WIDTH_M / 2 - GOAL_HALF_WIDTH_M - point["y_m"],
        goal_x - point["x_m"],
    )
    angle_delta = abs(math.degrees(angle_top - angle_bottom))
    angle_deg = min(angle_delta, 360 - angle_delta)

    # This is an inspectable teaching formula, not a calibrated football model.
    log_odds = (
        -1.55
        + (16 - distance_m) * 0.085
        + (angle_deg - 30) * 0.028
        - 0.28 * min(defenders_nearby, 3)
        - (0.65 if body_part == "head" else 0)
        + (1.35 if play_type == "penalty" else 0)
        + (0.18 if play_type == "counter" else 0)
    )
    probability = 1 / (1 + math.exp(-log_odds))
    return {
        "xg": round(max(0.01, min(0.95, probability)), 3),
        "distance_m": round(distance_m, 1),
        "angle_deg": round(angle_deg, 1),
        "nearby_defenders": defenders_nearby,
        "body_part": body_part,
        "play_type": play_type,
        "reason": None,
    }


def _pressure_condition(frame: dict, meta: dict) -> tuple[str, str, str] | None:
    payload = frame["payload"]
    pressured_team = payload.get("possession_team_id")
    carrier_id = payload.get("controlling_player_id")
    ball = payload.get("ball")
    if payload.get("ball_status") != "controlled" or not pressured_team or not carrier_id or not ball:
        return None

    players = {
        player["player_id"]: player
        for player in payload.get("players", [])
    }
    carrier = players.get(carrier_id)
    if not carrier:
        return None
    for player in payload.get("players", []):
        profile = next((row for row in meta["players"] if row["id"] == player["player_id"]), None)
        if (
            player["team_id"] != pressured_team
            and profile
            and profile.get("role") != "keeper"
            and _distance(player, carrier) <= PRESSURE_RADIUS_M
        ):
            return (player["team_id"], pressured_team, carrier_id)
    return None


def _pressure_episodes(meta: dict, frames: list[dict], cutoff_ms: int) -> dict:
    starts: list[dict] = []
    previous_key = None
    previous_time = None
    previous_period = None
    active_key = None
    for frame in frames:
        current_time = frame["timeline_ms"]
        current_key = _pressure_condition(frame, meta)
        continuous = (
            previous_time is not None
            and current_time - previous_time <= MAX_TRACKING_GAP_MS
            and frame["period"] == previous_period
        )
        if active_key is not None and (not continuous or current_key != active_key):
            active_key = None
        if current_key and continuous and current_key == previous_key and active_key is None:
            active_key = current_key
            starts.append({"time_ms": previous_time, "key": current_key, "period": frame["period"]})
        previous_key = current_key
        previous_time = current_time
        previous_period = frame["period"]

    outcomes = {
        "pressing_team_gained_possession": 0,
        "pressured_team_kept_and_progressed": 0,
        "pressured_team_kept_no_clear_progress": 0,
        "incomplete": 0,
        "pending": 0,
    }
    episodes = []
    for index, start in enumerate(starts, 1):
        end_ms = start["time_ms"] + PRESSURE_OUTCOME_MS
        episode = {
            "id": f"pressure-{index}",
            "time_ms": start["time_ms"],
            "pressing_team_id": start["key"][0],
            "pressured_team_id": start["key"][1],
            "carrier_id": start["key"][2],
            "outcome": "pending",
            "progression_m": None,
            "window_end_ms": end_ms,
        }
        if cutoff_ms < end_ms:
            outcomes["pending"] += 1
            episodes.append(episode)
            continue

        window = [frame for frame in frames if start["time_ms"] <= frame["timeline_ms"] <= end_ms]
        complete = (
            bool(window)
            and window[0]["timeline_ms"] == start["time_ms"]
            and window[-1]["timeline_ms"] == end_ms
            and all(
                frame["period"] == start["period"]
                for frame in window
            )
            and all(
                right["timeline_ms"] - left["timeline_ms"] <= MAX_TRACKING_GAP_MS
                for left, right in zip(window, window[1:])
            )
            and all(
                frame["payload"].get("possession_team_id") is not None
                and frame["payload"].get("ball") is not None
                and frame["payload"].get("ball_status") in {"controlled", "in_flight"}
                for frame in window
            )
        )
        if not complete:
            episode["outcome"] = "incomplete"
        else:
            possessions = [frame["payload"]["possession_team_id"] for frame in window]
            pressing_team, pressured_team, _ = start["key"]
            if pressing_team in possessions[1:]:
                episode["outcome"] = "pressing_team_gained_possession"
            elif all(team_id == pressured_team for team_id in possessions):
                sign = _period_direction(meta, start["period"], pressured_team)
                start_ball = window[0]["payload"]["ball"]
                end_ball = window[-1]["payload"]["ball"]
                progression = sign * (end_ball["x_m"] - start_ball["x_m"])
                episode["progression_m"] = round(progression, 1)
                episode["outcome"] = (
                    "pressured_team_kept_and_progressed"
                    if progression >= PRESSURE_PROGRESS_M
                    else "pressured_team_kept_no_clear_progress"
                )
            else:
                episode["outcome"] = "incomplete"
        outcomes[episode["outcome"]] += 1
        episodes.append(episode)

    known = sum(outcomes[key] for key in outcomes if key not in {"incomplete", "pending"})
    return {
        "definition": {
            "radius_m": PRESSURE_RADIUS_M,
            "consecutive_frames": 2,
            "outcome_window_ms": PRESSURE_OUTCOME_MS,
            "progression_threshold_m": PRESSURE_PROGRESS_M,
            "note": "Observed sequences only; they do not show that pressure caused the possession change.",
        },
        "episodes": episodes,
        "summary": {
            "total": len(episodes),
            "known": known,
            "pending": outcomes["pending"],
            "incomplete": outcomes["incomplete"],
            "regains": outcomes["pressing_team_gained_possession"],
            "outcomes": outcomes,
        },
    }


def build_live_insights(meta: dict, messages: list[dict], cutoff_ms: int) -> dict:
    """Calculate only metrics supported by observations delivered by match time."""
    observations = available(messages, cutoff_ms)
    frames = _frames_at(observations)
    teams = {team["id"]: team for team in meta["teams"]}
    players = {player["id"]: player for player in meta["players"]}
    contributions = {
        player_id: {
            **profile,
            "progressive_passes_completed": 0,
            "progressive_passes_attempted": 0,
            "passes_completed": 0,
            "recoveries": 0,
            "shots": 0,
            "confirmed_goals": 0,
            "xg": 0.0,
            "xg_shots": 0,
        }
        for player_id, profile in players.items()
    }

    starts = latest_events(observations, cutoff_ms, "pass_started", "pass_id")
    ends = latest_events(observations, cutoff_ms, "pass_resolved", "pass_id")
    for pass_id, start in starts.items():
        end = ends.get(pass_id)
        if not end:
            continue
        player_id = start["payload"].get("player_id")
        team_id = start["payload"].get("team_id")
        if player_id not in contributions or players[player_id]["team_id"] != team_id:
            continue
        if end["payload"]["details"].get("outcome") == "received" and end["payload"]["details"].get("controlling_team_id") == team_id:
            contributions[player_id]["passes_completed"] += 1
        period_sign = _period_direction(meta, start["period"], team_id)
        beginning = start["payload"]["details"].get("start_position")
        ending = end["payload"]["details"].get("end_position")
        if not beginning or not ending:
            continue
        forward_m = period_sign * (ending["x_m"] - beginning["x_m"])
        if forward_m >= PROGRESSIVE_PASS_M:
            contributions[player_id]["progressive_passes_attempted"] += 1
            if (
                end["payload"]["details"].get("outcome") == "received"
                and end["payload"]["details"].get("controlling_team_id") == team_id
            ):
                contributions[player_id]["progressive_passes_completed"] += 1

    recovery_events = latest_events(observations, cutoff_ms, "ball_recovered", "incident_id")
    for message in recovery_events.values():
        player_id = message["payload"].get("player_id")
        team_id = message["payload"].get("team_id")
        if player_id in contributions and players[player_id]["team_id"] == team_id:
            contributions[player_id]["recoveries"] += 1

    shot_starts = latest_events(observations, cutoff_ms, "shot_started", "shot_id")
    shot_ends = latest_events(observations, cutoff_ms, "shot_resolved", "shot_id")
    goals = latest_events(observations, cutoff_ms, "goal_status_changed", "goal_id")
    goal_by_shot = {}
    for goal in sorted(goals.values(), key=lambda row: (row["available_at_ms"], row["revision"])):
        shot_id = goal["payload"]["details"].get("shot_id")
        if shot_id:
            goal_by_shot[shot_id] = goal["payload"]["details"]["status"]
    shots = []
    for shot_id, start in shot_starts.items():
        payload = start["payload"]
        team_id = payload.get("team_id")
        if team_id not in teams:
            continue
        player_id = payload.get("player_id")
        resolved = shot_ends.get(shot_id)
        outcome = "pending"
        if resolved:
            source_outcome = resolved["payload"]["details"].get("outcome", "unknown")
            if source_outcome == "goal":
                status = goal_by_shot.get(shot_id)
                outcome = "goal" if status == "confirmed" else "cancelled" if status == "cancelled" else "pending_confirmation"
            else:
                outcome = source_outcome
        estimate = _xg_estimate(meta, frames, start, team_id)
        shot = {
            "id": shot_id,
            "time_ms": start["timeline_ms"],
            "team_id": team_id,
            "team_name": teams[team_id]["name"],
            "player_id": player_id if player_id in players and players[player_id]["team_id"] == team_id else None,
            "player_name": players[player_id]["name"] if player_id in players and players[player_id]["team_id"] == team_id else None,
            "outcome": outcome,
            "location": payload["details"].get("location"),
            **estimate,
        }
        shots.append(shot)
        if shot["player_id"]:
            row = contributions[shot["player_id"]]
            row["shots"] += 1
            if outcome == "goal":
                row["confirmed_goals"] += 1
            if estimate["xg"] is not None:
                row["xg"] += estimate["xg"]
                row["xg_shots"] += 1

    team_summaries = []
    for team_id, team in teams.items():
        team_shots = [shot for shot in shots if shot["team_id"] == team_id]
        team_summaries.append({
            "team_id": team_id,
            "team_name": team["name"],
            "shots": len(team_shots),
            "confirmed_goals": sum(shot["outcome"] == "goal" for shot in team_shots),
            "xg": round(sum(shot["xg"] or 0 for shot in team_shots), 3),
            "xg_shots": sum(shot["xg"] is not None for shot in team_shots),
        })

    return {
        "match_id": meta["match_id"],
        "clock_ms": cutoff_ms,
        "synthetic": True,
        "progressive_pass_threshold_m": PROGRESSIVE_PASS_M,
        "players": [
            row for row in contributions.values()
            if any(row[key] for key in (
                "progressive_passes_attempted", "recoveries", "shots"
            ))
        ],
        "shots": sorted(shots, key=lambda shot: (shot["time_ms"], shot["id"])),
        "shooting": {
            "teams": team_summaries,
            "xg_model_version": XG_VERSION,
            "xg_label": "Illustrative xG",
            "xg_note": (
                "An educational estimate from shot location, goal angle, nearby tracked defenders, body part and play type. "
                "Shots missing any required input are left unestimated. The formula is not trained or calibrated on real football."
            ),
        },
        "pressure": _pressure_episodes(meta, frames, cutoff_ms),
    }
