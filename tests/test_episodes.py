"""New development data gates; original source/reference expectations unchanged."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import uuid

import pytest
from fastapi.testclient import TestClient

from engine.catalog import list_matches
from engine.core import available, digest, pass_metrics
from engine.event_metrics import event_metrics, possession_window
from engine.match_state import match_state
from engine.pressure import pressure_metrics
from engine.repository import Repository
from evals.episodes import evaluate, load
from simulator.episodes import CASES, Case, build, encoded, export
from simulator.episode_validation import validate

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('case',CASES,ids=lambda c:c.case_id)
@pytest.mark.parametrize('faults',[False,True],ids=['source','delivery'])
def test_exported_observations_are_reproducible_valid_and_source_only(case,faults):
    dataset=build(case,faults)
    raw_meta,raw_stream=encoded(dataset)
    folder=ROOT/'data/runtime'/case.match_id(faults)
    assert raw_meta==(folder/'match.json').read_bytes()
    assert raw_stream==(folder/'stream.jsonl.gz').read_bytes()
    report=validate(dataset.metadata,dataset.observations)
    assert report['passed'],report['failures']
    assert report['diagnostics']['maximum_player_acceleration_mps2']<=6.05
    assert set(folder.iterdir())=={folder/'match.json',folder/'stream.jsonl.gz'}
    raw=json.dumps([dataset.metadata,dataset.observations])
    for forbidden in ('expected','parent_seed','fault_plan','paired_relations','d01','d02','d03','d04','d05','d06'):
        # Opaque UUID-derived identifiers may contain character fragments, so
        # inspect field/value tokens rather than arbitrary hexadecimal substrings.
        assert f'"{forbidden}"' not in raw
    for keeper in report['diagnostics']['keeper_ranges'].values():
        assert keeper['x_m'][1]-keeper['x_m'][0]>.1
        # Central build-up can keep the keeper's lateral position unchanged.
        # Do not demand artificial sideways movement just to animate the pitch.


def test_all_hand_authored_reference_checks_and_coverage():
    report=evaluate()
    assert report['reference_passed']==report['reference_checkpoints']==32,report['references']
    assert report['source_views_passed']==24
    assert (report['structural_parents'],report['specification_cases'],report['held_out_parents'])==(6,12,0)
    assert all(report['family_cases'][family] for family in ('pass','pressure','shot','goal','recovery','possession'))


def test_export_is_additive_and_refuses_overwriting_changed_new_source(tmp_path):
    (tmp_path/'data/runtime').mkdir(parents=True)
    sentinel=tmp_path/'data/runtime/legacy.txt';sentinel.write_text('preserve')
    export(tmp_path)
    first=tmp_path/'data/runtime'/CASES[0].match_id()/'match.json'
    first.write_text('changed')
    with pytest.raises(ValueError,match='immutable_export_conflict'):export(tmp_path)
    assert first.read_text()=='changed' and sentinel.read_text()=='preserve'


def test_parent_structure_split_and_no_runtime_reference_import():
    manifest=json.loads((ROOT/'data/provenance/episodes-v1.json').read_text())
    assert len({c['parent'] for c in manifest['cases']})==6
    assert len({c['case_id'] for c in manifest['cases']})==12
    assert len({c['match_id'] for c in manifest['cases']})==24
    assert {c['split'] for c in manifest['cases']}=={'development'}
    from simulator.episode_scenes import scene_for
    # Different parents have different event topology/paths, not just new seeds.
    structures=[digest({'paths':scene_for(n).paths,'segments':scene_for(n).segments}) for n in range(1,7)]
    assert len(set(structures))==6
    for path in [*ROOT.glob('engine/*.py'),ROOT/'services/api/main.py']:
        source=path.read_text()
        assert 'simulator.episode' not in source and 'evaluation-only/episodes' not in source
    assert all('independent_football_review' not in r for r in list_matches(True,True))
    profile=(ROOT/'data/provenance/episode-profile-v1.json').read_bytes()
    assert hashlib.sha256(profile).hexdigest()==manifest['profile_sha256']
    for filename,expected in manifest['authoring_files_sha256'].items():
        assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==expected


def test_mirror_and_duplicate_names_preserve_measurements_not_parent_independence():
    dataset=build(Case(1));metadata,rows=deepcopy(dataset.metadata),deepcopy(dataset.observations)
    metadata['periods'][0]['attack_direction']={'blue':'left','amber':'right'}
    for player in metadata['players']:player['name']='Alex Marin'
    def mirror(value):
        if isinstance(value,dict):
            if 'x_m' in value:value['x_m']=round(105-value['x_m'],4)
            for item in value.values():mirror(item)
        if isinstance(value,list):
            for item in value:mirror(item)
    for row in rows:mirror(row['payload'])
    assert validate(metadata,rows)['passed']
    original=next(p for p in pass_metrics(dataset.observations,25000,dataset.metadata) if p['pass_id']=='p02')
    reflected=next(p for p in pass_metrics(rows,25000,metadata) if p['pass_id']=='p02')
    for key in ('eligible','receiver_id','progression_m','bypassed_count','pressure_opponents_max'):
        assert reflected[key]==original[key]
    a=pressure_metrics(dataset.metadata,dataset.observations,25000)[0]['facts']
    b=pressure_metrics(metadata,rows,25000)[0]['facts']
    assert b['forward_m']==a['forward_m']==24
    assert b['before']==a['before'] and b['after']==a['after']


def test_conflicting_duplicate_is_rejected_not_silently_counted():
    dataset=build(Case(1));rows=deepcopy(dataset.observations)
    changed=deepcopy(rows[0]);changed['payload']['possession_team_id']='amber'
    rows.append(changed)
    report=validate(dataset.metadata,rows)
    assert not report['passed']
    assert any(f.get('detail')=='conflicting_retransmission' for f in report['failures'])


def test_corrected_tracking_must_obey_new_profile_not_only_legacy_speed():
    dataset=build(Case(1));rows=deepcopy(dataset.observations)
    original=next(r for r in rows if r['kind']=='tracking_frame' and r['timeline_ms']==10100)
    corrected=deepcopy(original)
    corrected.update(message_id='changed-tracking',revision=2,supersedes_message_id=original['message_id'],
                     available_at_ms=40000,sequence_no=max(r['sequence_no'] for r in rows)+1)
    next(p for p in corrected['payload']['players'] if p['player_id']=='amber-02')['x_m']+=.15
    rows.append(corrected)
    report=validate(dataset.metadata,rows)
    assert report['legacy_feed']
    assert not report['passed']
    assert any(f['code']=='player_acceleration' and f.get('view')=='latest_correction' for f in report['failures'])


def test_keeper_targets_use_the_same_observed_ball_as_the_episode():
    dataset=build(Case(1))
    frames={r['timeline_ms']:r['payload'] for r in dataset.observations if r['kind']=='tracking_frame'}
    for t in (0,20000,30000,60000,90000):
        frame=frames[t];ball=frame['ball']
        for team in ('blue','amber'):
            keeper=next(p for p in frame['players'] if p['player_id']==team+'-01')
            depth=4+(ball['x_m'] if team=='blue' else 105-ball['x_m'])*.07
            assert keeper['x_m']==pytest.approx(depth if team=='blue' else 105-depth,abs=.0001)
            assert keeper['y_m']==pytest.approx(34+(ball['y_m']-34)*.22,abs=.0001)


def test_goal_optional_attribution_can_be_absent_without_inference_or_crash():
    dataset=build(Case(4));rows=deepcopy(dataset.observations)
    for row in rows:
        if row['kind']=='event' and row['payload']['type']=='goal_status_changed':
            row['payload']['details'].pop('scorer_id')
            row['payload']['details'].pop('shot_id')
    assert validate(dataset.metadata,rows)['passed']
    goals=[m for m in event_metrics(dataset.metadata,rows,36000) if m['family']=='goal']
    assert goals[0]['participants']['scorer'] is None


def test_speed_only_passes_a_join_that_new_acceleration_check_rejects():
    from simulator.validate import validate_feed
    dataset=build(Case(1));rows=deepcopy(dataset.observations)
    frame=next(r for r in rows if r['kind']=='tracking_frame' and r['timeline_ms']==10100)
    player=next(p for p in frame['payload']['players'] if p['player_id']=='amber-02')
    player['x_m']+=.15
    validate_feed(dataset.metadata,rows)
    report=validate(dataset.metadata,rows)
    assert 'player_acceleration' in {f['code'] for f in report['failures']}


def test_turn_limit_is_independent_of_speed_and_acceleration_checks():
    dataset=build(Case(1));rows=deepcopy(dataset.observations)
    for row in rows:
        if row['kind']!='tracking_frame':continue
        t=row['timeline_ms']/1000
        p=next(p for p in row['payload']['players'] if p['player_id']=='amber-02')
        p.update(x_m=83+.4*math.cos(3.75*t),y_m=18+.4*math.sin(3.75*t))
    report=validate(dataset.metadata,rows)
    codes={f['code'] for f in report['failures']}
    assert codes=={'player_turn'}


@pytest.mark.parametrize('mutation,expected',[
    ('shot_actor','release_actor_ball_alignment'),
    ('intervention','shot_intervention_alignment'),
    ('goal_team','goal_scorer_team'),
    ('roster','roster_profile'),
    ('direction','attack_direction'),
    ('future','future_observation'),
    ('control_team','acquisition_team_alignment'),
])
def test_invalid_examples_fail_the_intended_check(mutation,expected):
    dataset=build(Case(4) if mutation=='goal_team' else Case(2) if mutation=='control_team' else Case(3))
    meta,rows=deepcopy(dataset.metadata),deepcopy(dataset.observations)
    if mutation=='shot_actor':
        next(r for r in rows if r['kind']=='event' and r['payload']['type']=='shot_started')['payload']['player_id']='blue-08'
    if mutation=='intervention':
        next(r for r in rows if r['kind']=='event' and r['payload']['type']=='shot_resolved')['payload']['details']['outcome']='blocked'
    if mutation=='goal_team':
        for row in rows:
            if row['kind']=='event' and row['payload']['type']=='goal_status_changed':row['payload']['details']['scorer_id']='amber-09'
    if mutation=='roster':meta['players'][0]['role']='outfield'
    if mutation=='direction':meta['periods'][0]['attack_direction']['blue']='left'
    if mutation=='control_team':
        next(r for r in rows if r['kind']=='event' and r['payload']['type']=='ball_recovered')['payload']['team_id']='amber'
    report=validate(meta,rows,cutoff=1000 if mutation=='future' else None)
    assert expected in {f['code'] for f in report['failures']},report


def test_unknown_and_missing_time_are_not_filled_from_hidden_world():
    metadata,rows=load('d05-b')
    assert possession_window(metadata,rows,60000,60000)['unknown_ms']==4100
    assert not any(r['kind']=='tracking_frame' and 45000<=r['timeline_ms']<49000 for r in rows)
    assert all(r['payload']['ball'] is None and r['payload']['ball_status']=='unknown'
               for r in rows if r['kind']=='tracking_frame' and 65000<=r['timeline_ms']<68000)
    with_future=validate(metadata,rows,cutoff=60000)
    assert not with_future['passed']
    delivered=available(rows,60000)
    assert validate(metadata,delivered,cutoff=60000)['passed']


def test_delivery_faults_preserve_logical_events_and_corrected_score():
    clean_meta,clean=load('d04-b');fault_meta,faults=load('d04-b',True)
    assert len(faults)>len({r['message_id'] for r in faults})
    assert match_state(clean_meta,clean,52000)['score']==match_state(fault_meta,list(reversed(faults)),52000)['score']=={'blue':1,'amber':1}
    assert len([r for r in available(faults,90000) if r['kind']=='event'])==len([r for r in available(clean,90000) if r['kind']=='event'])
    assert not any(m['family']=='shot' for m in event_metrics(fault_meta,faults,33799))
    assert any(m['family']=='shot' for m in event_metrics(fault_meta,faults,33800))


def test_team_retention_does_not_imply_receivers_individual_control():
    metadata,rows=load('d06-a')
    p=next(p for p in pass_metrics(rows,19000,metadata) if p['pass_id']=='p01')
    assert p['eligible'] and p['receiver_id']=='blue-09' and p['retained']
    frame=next(r for r in available(rows,19000) if r['kind']=='tracking_frame' and r['timeline_ms']==19000)
    assert frame['payload']['controlling_player_id']=='blue-10'


def test_real_clock_period_excerpt_reverses_direction_without_compressing_halves():
    from evals.episode_protocol import period_excerpt
    metadata,rows=period_excerpt()
    report=validate(metadata,rows)
    assert report['passed'],report['failures']
    assert match_state(metadata,rows,2700000)['period_elapsed_ms']==2700000
    assert match_state(metadata,rows,3500000)['period_status']=='ended'
    assert match_state(metadata,rows,3600000)['period']==2
    assert match_state(metadata,rows,3601000)['period_elapsed_ms']==1000
    release=next(r for r in rows if r['kind']=='event' and r['payload']['type']=='pass_started')
    resolution=next(r for r in rows if r['kind']=='event' and r['payload']['type']=='pass_resolved')
    assert release['period']==resolution['period']==2
    assert resolution['payload']['details']['end_position']['x_m']<release['payload']['details']['start_position']['x_m']
    assert metadata['periods'][1]['timeline_offset_ms']-2700000==900000


@pytest.fixture
def episode_api(tmp_path,monkeypatch):
    from services.api import main
    ids={c.match_id(f) for c in CASES for f in (False,True)}
    monkeypatch.setattr(main,'repo',Repository(tmp_path/'episodes.db'))
    monkeypatch.setattr(main,'COVERAGE',True)
    monkeypatch.setattr(main,'DEVELOPMENT',True)
    monkeypatch.setattr(main,'DEVELOPMENT_IDS',ids)
    monkeypatch.setattr(main,'MIXED_IDS',main.MIXED_IDS|ids)
    monkeypatch.setattr(main,'PRESSURE_IDS',main.FLAGSHIP_IDS|ids)
    monkeypatch.setattr(main,'FOUNDRY',False)
    monkeypatch.setattr(main,'EVENT_MODEL',False)
    monkeypatch.setattr(main,'transport',None)
    monkeypatch.setattr(main,'JOBS',{})
    monkeypatch.setattr(main,'LIVE_MEASURED',{})
    return main


def test_development_catalogue_is_opt_in_and_never_changes_original_default(episode_api,monkeypatch):
    main=episode_api
    assert len(list_matches())==173
    assert len(list_matches(True))==181
    assert len(list_matches(True,True))==205
    assert list_matches(True,True)[:181]==list_matches(True)
    with TestClient(main.app) as client:
        assert len(client.get('/api/matches').json()['matches'])==205
        monkeypatch.setattr(main,'DEVELOPMENT',False)
        assert len(client.get('/api/matches').json()['matches'])==181
        result=client.post('/api/replay-sessions',headers={'X-Producer-Token':main.TOKEN},json={'match_id':CASES[0].match_id(),'mode':'guided','execution':'template'})
        assert result.status_code==422


@pytest.mark.parametrize('case,at,story,family,focus',[
    ('d01-a',25000,'story-p02','pass','blue-11'),
    ('d01-a',25000,'story-pressure-p02','pressure','blue-08'),
    ('d02-a',20000,'story-recovery-i01','recovery','blue-06'),
    ('d03-a',24000,'story-shot-s01','shot','blue-09'),
    ('d04-b',36000,'story-goal-g01','goal','blue-09'),
    ('d05-a',60000,'story-possession-60000','possession',None),
])
def test_new_families_keep_evidence_approval_variants_and_recap(episode_api,case,at,story,family,focus):
    main=episode_api
    c=next(c for c in CASES if c.case_id==case)
    head={'X-Producer-Token':main.TOKEN}
    with TestClient(main.app) as client:
        sid=client.post('/api/replay-sessions',headers=head,json={'match_id':c.match_id(),'mode':'guided','execution':'template'}).json()['session_id']
        base=f'/api/replay-sessions/{sid}'
        assert client.post(base+'/control',headers=head,json={'action':'seek','clock_ms':at}).status_code==200
        producer=client.get(base+'/snapshot',headers=head).json()
        assert story in [p['id'] for p in producer['stories']]
        assert client.get(base+'/snapshot').json()['stories']==[]
        evidence=client.get(base+f'/stories/{story}/evidence',headers=head).json()
        package=evidence['story']
        assert package.get('family','pass')==family
        original_hash=package['package_hash']
        assert client.get(base+f'/stories/{story}/evidence').status_code==404
        response=client.post(base+f'/stories/{story}/review',headers=head,json={
            'action':'approve','expected_revision':package['revision'],'package_hash':original_hash,
            'idempotency_key':str(uuid.uuid4())})
        assert response.status_code==200,response.text
        public=client.get(base+'/snapshot').json()
        assert any(p['id']==story for p in public['stories'])
        for language in ('en','es'):
            for detail in ('simple','detail'):
                params={'language':language,'detail':detail}
                if focus:params['focus']=focus
                variant=client.get(base+f'/stories/{story}/variants',params=params)
                assert variant.status_code==200 and variant.json()['text']
        recap=client.post(base+'/recaps',json={'through_ms':at}).json()
        assert any(p['story_id']==story for p in recap['moments'])
        # Reopen persistence without changing the approved package.
        reopened=Repository(main.repo.path)
        assert reopened.latest_package(sid,story)['package_hash']==original_hash
        if family=='goal':
            assert producer['score']=={'blue':2,'amber':1}
            client.post(base+'/control',headers=head,json={'action':'seek','clock_ms':52000})
            corrected=client.get(base+'/snapshot').json()
            assert corrected['score']=={'blue':1,'amber':1}
            assert not any(p['id']==story for p in corrected['stories'])
            assert not any(p['story_id']==story for p in client.post(base+'/recaps',json={}).json()['moments'])
            assert reopened.stored_package(sid,story,package['revision'])['package_hash']==original_hash
