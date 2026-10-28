from engine.fan_insights import build_demo_insights


def test_synthetic_insight_demo_keeps_outcomes_and_sources_consistent():
    demo = build_demo_insights()

    assert len(demo["xg"]["shots"]) == sum(team["shots"] for team in demo["xg"]["teams"])
    assert all(0 < shot["xg"] < 1 for shot in demo["xg"]["shots"])
    assert demo["pressure"]["summary"]["total"] == sum(demo["pressure"]["summary"]["outcomes"].values())
    assert demo["pressure"]["summary"]["known"] + demo["pressure"]["summary"]["incomplete"] == demo["pressure"]["summary"]["total"]
    assert all(scenario["trigger_observed"] for scenario in demo["tactics"]["scenarios"])
    assert all(len(scenario["frame"]["players"]) == 22 for scenario in demo["tactics"]["scenarios"])
    assert {shot["player_id"] for shot in demo["xg"]["shots"]}.issubset({player["player_id"] for player in demo["players"]})
