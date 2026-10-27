from copy import deepcopy

from engine.core import metric
from engine.workflow import EvidenceTools, run_workflow
from simulator.generate import generate


def test_receiver_is_not_credited_with_team_retention_after_passing_onward():
    meta, rows = generate()
    rows = deepcopy(rows)
    # The observation stream says the team retains, but another player now controls.
    for row in rows:
        if row['kind'] == 'tracking_frame' and 20000 <= row['timeline_ms'] <= 22200:
            row['payload']['controlling_player_id'] = 'blue-09'
    assert metric(rows, 25000, meta)['retained'] is True
    package = run_workflow(EvidenceTools(meta, rows, 25000))
    receiver = package['metrics']['receiver_id']
    texts = {v['language']: v['text'] for v in package['variants']
             if v['focus'] == receiver and v['detail'] == 'simple'}
    assert 'received the pass; Club del Faro retained possession' in texts['en']
    assert 'recibió el pase; Club del Faro conservó la posesión' in texts['es']
    assert 'received the pass and kept possession' not in texts['en']


def test_team_turnover_within_window_produces_no_retention_story():
    meta, rows = generate()
    rows = deepcopy(rows)
    next(row for row in rows if row['kind'] == 'tracking_frame'
         and row['timeline_ms'] == 21000)['payload']['possession_team_id'] = 'amber'
    assert run_workflow(EvidenceTools(meta, rows, 25000)) is None
