"""Independent hand references for the proximity measure; not football usefulness."""
from copy import deepcopy
from functools import lru_cache
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import pytest
from engine.pressure import proximity_window, pressure_metrics
from engine.event_narrative import build_event_package, EventPackage
from engine.core import digest, pass_metrics
from engine.overlay_policy import choose_overlay
from engine.recap import project_recap
from simulator.flagship import build
from simulator.suite import serialize
from simulator.validate import validate_feed
from test_match_coverage import store, client, create, at, package, review, HEAD
from services.api import main

ROOT=Path(__file__).resolve().parents[1]

@lru_cache
def fixture(correction=False):return build(correction)

def hand_window():
    # Two known opponents at 1m/2m for 1s, then both at 20m for 1s.
    meta={'players':[{'id':'p','team_id':'blue'},{'id':'a','team_id':'amber'},{'id':'b','team_id':'amber'}]}
    rows=[]
    for t in range(0,2001,100):
        rows.append({'kind':'tracking_frame','message_id':f'f{t}','timeline_ms':t,'available_at_ms':t,'sequence_no':t,'revision':1,'period':1,'supersedes_message_id':None,
            'payload':{'controlling_player_id':'p','possession_team_id':'blue','ball_status':'controlled','players':[
            {'player_id':'p','x_m':0,'y_m':0}, {'player_id':'a','x_m':1 if t<1000 else 20,'y_m':0}, {'player_id':'b','x_m':2 if t<1000 else 20,'y_m':0}]}})
    return meta,rows


def test_time_weighting_independent_reference_duplicate_and_reorder():
    meta,rows=hand_window()
    # Unequal observation density must not change 2*1s + 0*1s / 2s = 1.
    rows=[r for r in rows if r['timeline_ms']>=1000 or r['timeline_ms']%200==0]
    for source in [rows,list(reversed(rows))+rows]:
        value,_=proximity_window(meta,source,2000,0,2000,'p','blue')
        assert value=={'start_ms':0,'end_ms':2000,'known_ms':2000,'coverage':1,'mean':1}

@pytest.mark.parametrize('missing',['gap','opponent','actor','control','team'])
def test_missing_observation_never_counts_as_zero_pressure(missing):
    meta,rows=hand_window()
    if missing=='gap':rows=[r for r in rows if not 500<=r['timeline_ms']<1000]
    else:
        for r in rows:
            if 500<=r['timeline_ms']<=1000:
                if missing in {'opponent','actor'}:r['payload']['players']=[p for p in r['payload']['players'] if p['player_id']!=('a' if missing=='opponent' else 'p')]
                elif missing=='control':r['payload']['controlling_player_id']=None
                else:r['payload']['possession_team_id']=None
    value,_=proximity_window(meta,rows,2000,0,2000,'p','blue')
    assert value['coverage']<.95

@pytest.mark.parametrize('correction',[False,True])
def test_new_sources_reproducible_physical_and_all_existing_families(correction):
    from engine.event_metrics import event_metrics
    meta,rows=fixture(correction)
    assert validate_feed(meta,rows)['active_players']==22
    assert gzip.compress(serialize(rows).encode(),mtime=0)==(ROOT/'data/runtime'/meta['match_id']/'stream.jsonl.gz').read_bytes()
    assert len([p for p in pass_metrics(rows,105000,meta) if p['eligible']])==4
    assert {m['family'] for m in event_metrics(meta,rows,105000)}=={'goal','shot','recovery','possession'}
    # These are authored independent reference values, not labels read by production.
    value=next(m for m in pressure_metrics(meta,rows,92000) if m['subject_id']=='pass-4')
    f=value['facts']
    assert (f['before']['mean'],f['after']['mean'],f['drop'],f['forward_m'])==(2,.4,1.6,30)
    assert f['before']['coverage']==f['after']['coverage']==1
    assert f['stands_out'] and sorted(c['forward_m'] for c in f['comparators'])==[18,22,25]
    assert not any(m['subject_id']=='pass-4' for m in pressure_metrics(meta,rows,91299))
    p=build_event_package(value,meta)
    assert p['schema_version']=='6.0.0'
    assert 'pasó 30.0 m' in next(v['text'] for v in p['variants'] if v['language']=='es' and v['detail']=='simple')
    assert 'Passer:' in next(v['text'] for v in p['variants'] if v['language']=='en' and v['focus']=='blue-11')
    assert 'Receiver:' in next(v['text'] for v in p['variants'] if v['language']=='en' and v['focus']=='blue-09')

@pytest.mark.parametrize('failure',['missing_after','unknown_control','no_drop','short_pass','retention_lost','unresolved'])
def test_full_pipeline_abstains_without_required_evidence(failure):
    meta,source=fixture();rows=deepcopy(source)
    for r in rows:
        if r['kind']=='tracking_frame':
            if 88300<=r['timeline_ms']<=90300:
                if failure=='missing_after':r['payload']['players']=[]
                if failure=='unknown_control':r['payload']['controlling_player_id']=None
                if failure=='no_drop':
                    receiver=next(p for p in r['payload']['players'] if p['player_id']=='blue-09')
                    for p in r['payload']['players']:
                        if p['player_id'] in {'amber-06','amber-07','amber-08'}:p.update(x_m=receiver['x_m']+1,y_m=receiver['y_m'])
            if failure=='retention_lost' and r['timeline_ms']==91000:r['payload']['possession_team_id']='amber'
        elif r['kind']=='event' and r['payload']['type']=='pass_resolved' and r['payload']['details']['pass_id']=='pass-4':
            if failure=='short_pass':r['payload']['details']['end_position']['x_m']=30
            if failure=='unresolved':r['available_at_ms']=250000
    assert not any(m['subject_id']=='pass-4' for m in pressure_metrics(meta,rows,92000))


def test_source_revision_changes_only_affected_evidence_and_rejects_forgery():
    meta,source=fixture();before=pressure_metrics(meta,source,92000)
    original=next(r for r in source if r['kind']=='tracking_frame' and r['timeline_ms']==89000)
    corrected=deepcopy(original);corrected.update(message_id='corrected-pressure',revision=2,supersedes_message_id=original['message_id'],available_at_ms=94000)
    after=pressure_metrics(meta,source+[corrected],94000)
    assert [p['evidence_revision'] for p in before[:3]]==[p['evidence_revision'] for p in after[:3]]
    assert before[-1]['evidence_revision']!=after[-1]['evidence_revision']
    p=build_event_package(before[-1],meta)
    for key,value in [('drop',100),('stands_out',False),('radius_m',10)]:
        forged=deepcopy(p);forged['metrics']['facts'][key]=value;forged['package_hash']=digest({k:v for k,v in forged.items() if k!='package_hash'})
        with pytest.raises(ValueError):EventPackage.model_validate(forged)


def test_all_old_source_exports_keep_hashes():
    for name in ['match-coverage.json','matchday-demo-v2.json']:
        for c in json.loads((ROOT/'data/provenance'/name).read_text())['cases']:
            assert hashlib.sha256((ROOT/'data/runtime'/c['match_id']/'stream.jsonl.gz').read_bytes()).hexdigest()==c['sha256']


def test_overlay_hold_goal_preemption_withdrawal_and_exact_revision():
    shot={'id':'shot','revision':1,'package_hash':'s','family':'shot','eligible_from_ms':0,'metrics':{}}
    pressure={**shot,'id':'pressure','family':'pressure','package_hash':'p'}
    previous={'id':'pressure','revision':1,'package_hash':'p','shown_at_ms':0}
    assert choose_overlay([pressure,shot],previous,7999)==pressure
    assert choose_overlay([pressure,shot],previous,8000)==shot
    goal={**shot,'family':'goal','id':'goal'}
    assert choose_overlay([pressure,goal],previous,100)==goal
    assert choose_overlay([shot],previous,100)==shot
    assert choose_overlay([{**pressure,'revision':2},shot],previous,100)==shot
    assert choose_overlay([],previous,100) is None


def test_pressure_real_api_approval_bilingual_focus_recap_restart_and_invalidation(client,monkeypatch):
    from engine.repository import Repository
    sid=create(client,'match-0c0a000000000005');at(sid,92000)
    p=package(client,sid,'story-pressure-pass-4')
    assert client.get(f'/api/replay-sessions/{sid}/stories/{p["id"]}/evidence').status_code==404
    assert review(client,sid,p).status_code==200
    assert client.get(f'/api/replay-sessions/{sid}/stories/{p["id"]}/variants?language=es&detail=detail&focus=blue-09').status_code==200
    snapshot=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert snapshot['flagship_demo'] and snapshot['story']['family']=='pressure'
    assert '2.0 to 0.4' in snapshot['story']['why_now']['en']
    assert snapshot['story']['evidence_state']=='complete'
    # Linked ordinary pass and pressure insight collapse to one approved incident.
    oldpass=package(client,sid,'story-pass-4');assert review(client,sid,oldpass).status_code==200
    recap=client.post(f'/api/replay-sessions/{sid}/recaps',json={}).json()
    assert recap['approved_count']==1 and recap['moments'][0]['family']=='pressure'
    assert client.post(f'/api/replay-sessions/{sid}/recaps',json={'focus':'blue-01'}).json()['approved_count']==0
    # Reopening persistence preserves exact schema/hash and approval.
    from engine.cloud_repository import CosmosRepository
    reopened=Repository(main.repo.path) if isinstance(main.repo,Repository) else CosmosRepository(client=main.repo.client)
    monkeypatch.setattr(main,'repo',reopened)
    assert package(client,sid,p['id'])==p
    assert main.repo.decision(sid,p['id'])['status']=='approved'
    meta,rows=fixture();original=next(r for r in rows if r['kind']=='tracking_frame' and r['timeline_ms']==89000)
    corrected=deepcopy(original);corrected.update(message_id='late-pressure',revision=2,supersedes_message_id=original['message_id'],available_at_ms=94000)
    orig_inputs=main.inputs
    monkeypatch.setattr(main,'inputs',lambda s,t:(meta,rows+[corrected]) if s['id']==sid else orig_inputs(s,t))
    at(sid,94000)
    snapshot=client.get(f'/api/replay-sessions/{sid}/snapshot').json()
    assert all(s['id']!=p['id'] for s in snapshot['stories'])
    assert main.repo.decision(sid,p['id'])['status']=='superseded'
    assert main.repo.stored_package(sid,p['id'],1)==p

@pytest.mark.parametrize('bad',[False,True])
def test_v6_existing_director_reviewer_supported_and_invalid_selection_fallback(bad):
    from engine.structured_workflow import run_event_workflow
    from engine.workflow import EvidenceTools
    class Provider:
        async def complete(self,role,instructions,payload,schema,max_tokens):
            return {'action':'propose' if role=='Story Director' else 'supported','claim_ids':['invented'] if bad else ['c-event'],'reason':'supplied observations only'},{'input_token_count':20,'output_token_count':20,'total_token_count':40}
    meta,rows=fixture();p=run_event_workflow(EvidenceTools(meta,rows,92000),'pressure','pass-4',provider=Provider())
    assert p['schema_version']=='6.0.0'
    assert p['mode']==('template fallback' if bad else 'Microsoft Agent Framework + Azure OpenAI')
    EventPackage.model_validate(p)


def test_model_mode_can_start_without_undefined_flag_dependency():
    result=subprocess.run([str(ROOT/'.venv313/bin/python'),'-c','import services.api.main'],cwd=ROOT,env={**os.environ,'WHY_NOW_MATCH_MODEL':'1','WHY_NOW_MODEL_MODE':'foundry','WHY_NOW_DB':':memory:'},capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_unknown_shot_has_unconfirmed_relevance_and_machine_readable_state():
    from engine.explainability import evidence_state,why_now
    p={'family':'shot','metrics':{'facts':{'outcome':'unknown','location':None},'participants':{'shooter':None}}}
    assert evidence_state(p)=='awaiting_outcome'
    assert 'unconfirmed' in why_now(p)
    assert 'sin confirmar' in why_now(p,'es')


def test_late_observations_do_not_leak_and_period_start_is_a_boundary():
    meta,rows=hand_window();delayed=deepcopy(rows)
    delayed[-1]['available_at_ms']=2500
    value,_=proximity_window(meta,delayed,2000,0,2000,'p','blue')
    assert value['coverage']==.95
    value,_=proximity_window(meta,delayed,2500,0,2000,'p','blue')
    assert value['coverage']==1
    m,source=fixture();changed=deepcopy(m)
    changed['periods'].append({**changed['periods'][0],'period':2,'timeline_offset_ms':86000})
    boundary_rows=deepcopy(source)
    for row in boundary_rows:
        if row['timeline_ms']>=86000:row.update(period=2,period_elapsed_ms=row['timeline_ms']-86000)
    assert not any(p['subject_id']=='pass-4' for p in pressure_metrics(changed,boundary_rows,92000))


def test_leftward_attack_uses_signed_displacement_without_changing_counts():
    meta,source=fixture();meta=deepcopy(meta);rows=deepcopy(source)
    for period in meta['periods']:period['attack_direction']={k:'left' if v=='right' else 'right' for k,v in period['attack_direction'].items()}
    for r in rows:
        if r['kind']=='tracking_frame':
            for p in r['payload']['players']:p['x_m']=105-p['x_m']
            if r['payload']['ball']:r['payload']['ball']['x_m']=105-r['payload']['ball']['x_m']
        elif r['kind']=='event':
            for key in ['start_position','end_position','location']:
                p=r['payload']['details'].get(key)
                if p:p['x_m']=105-p['x_m']
    value=next(m for m in pressure_metrics(meta,rows,92000) if m['subject_id']=='pass-4')
    assert value['facts']['forward_m']==30
    assert value['facts']['before']['mean']==2 and value['facts']['after']['mean']==.4


def test_v6_new_sessions_disabled_on_rollback_existing_approvals_remain(client,monkeypatch):
    sid=create(client,'match-0c0a000000000005');at(sid,92000)
    p=package(client,sid,'story-pressure-pass-4');assert review(client,sid,p).status_code==200
    monkeypatch.setattr(main,'COVERAGE',False)
    assert package(client,sid,p['id'])==p
    assert client.get(f'/api/replay-sessions/{sid}/snapshot').json()['story']['id']==p['id']
    assert client.post('/api/replay-sessions',headers=HEAD,json={'match_id':'match-0c0a000000000005'}).status_code==422


def test_authored_recoveries_align_with_observed_carrier_at_acquisition():
    meta,rows=fixture();frames={r['timeline_ms']:r['payload'] for r in rows if r['kind']=='tracking_frame'}
    for r in rows:
        if r['kind']=='event' and r['payload']['type']=='ball_recovered':
            assert frames[r['timeline_ms']]['controlling_player_id']==r['payload']['player_id']
