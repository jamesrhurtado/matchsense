"""Hand-authored paired histories; expectations do not call the production selector."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from engine.context import recent_pass_context
from engine.contextual_narrative import build_contextual_package
from engine.contracts import PublicationPackage
from engine.core import load_match, digest
from engine.workflow import EvidenceTools, ToolError


def scene(distances=(5, 7, 10)):
    meta, original = load_match('match-001')
    meta, rows = deepcopy(meta), deepcopy(original)
    start = next(r for r in rows if r['kind'] == 'event' and r['payload']['type'] == 'pass_started')
    end = next(r for r in rows if r['kind'] == 'event' and r['payload']['type'] == 'pass_resolved')
    for index, distance in enumerate(distances):
        for template, kind, at in [(start, 'start', 1000 + index*2000), (end, 'end', 2000 + index*2000)]:
            row = deepcopy(template)
            row.update(message_id=f'history-{index}-{kind}', timeline_ms=at, period_elapsed_ms=at,
                       available_at_ms=at, sequence_no=10000+index*2+(kind=='end'))
            row['payload']['event_id'] = row['message_id']
            row['payload']['details']['pass_id'] = f'history-{index}'
            if kind == 'start':
                row['payload']['details']['start_position'] = {'x_m': 20, 'y_m': 30}
            else:
                row['payload']['details']['end_position'] = {'x_m': 20+distance, 'y_m': 30}
            rows.append(row)
    return meta, rows


def get(meta, rows, cutoff=25000):
    return recent_pass_context(meta, rows, cutoff, 'pass-1')


def test_paired_histories_change_interpretation_with_identical_present_play():
    ma, a = scene(); mb, b = scene((20, 21, 22))
    ca, cb = get(ma, a), get(mb, b)
    assert ca['status'] == cb['status'] == 'available'
    assert [p['pass_id'] for p in ca['comparators']] == ['history-2', 'history-1', 'history-0']
    assert [p['forward_m'] for p in ca['comparators']] == [10, 7, 5]
    assert ca['relation'] == 'greater_than_each' and cb['relation'] == 'no_comparative_claim'
    pa = build_contextual_package(EvidenceTools(ma, a, 25000, 'pass-1'))
    pb = build_contextual_package(EvidenceTools(mb, b, 25000, 'pass-1'))
    assert pa['metrics']['forward_pass_m'] == pb['metrics']['forward_pass_m']
    assert pa['narrative_plan']['angle'] == 'historical_contrast'
    assert 'previous three completed passes in this replay' in pa['variants'][0]['text']
    assert 'previous three' not in pb['variants'][0]['text']
    assert 'tres pases completados anteriores' in next(v['text'] for v in pa['variants'] if v['id']=='es_simple_general')


def test_cutoff_correction_retransmission_and_excluded_population():
    meta, rows = scene()
    target = next(r for r in rows if r['message_id']=='history-2-end')
    correction = deepcopy(target)
    correction.update(message_id='corrected-history', supersedes_message_id=target['message_id'],
                      revision=2, sequence_no=99999, available_at_ms=26000)
    correction['payload']['details']['end_position']['x_m'] = 60
    before = get(meta, rows)
    assert get(meta, rows+[deepcopy(target), correction]) == before
    after = get(meta, rows+[correction], 27000)
    assert after['relation'] == 'no_comparative_claim' and after['revision'] != before['revision']
    target['payload']['details']['outcome'] = 'intercepted'
    excluded = get(meta, rows)
    assert excluded['status'] == 'insufficient_history'
    correction['payload']['details']['end_position']['x_m'] = 22
    assert get(meta, rows+[correction], 27000)['relation'] == 'greater_than_each'


def test_late_insertion_and_ties_have_stable_exact_population():
    meta, rows = scene((1, 2, 3, 25))
    for r in rows:
        if r['message_id'].startswith('history-3'):
            r['available_at_ms'] = 26000
    before = get(meta, rows)
    after = get(meta, rows, 27000)
    assert before['relation'] == 'greater_than_each' and after['relation'] == 'no_comparative_claim'
    assert [p['pass_id'] for p in after['comparators']] == ['history-3', 'history-2', 'history-1']
    for r in rows:
        if r['message_id'].startswith('history-') and r['payload']['type']=='pass_resolved':
            r.update(timeline_ms=10000, available_at_ms=10000)
    assert [p['pass_id'] for p in get(meta, rows)['comparators']] == ['history-0', 'history-1', 'history-2']


def test_missing_tracking_unpaired_endpoint_and_period_boundary_abstain():
    meta, rows = scene()
    gap = [r for r in rows if not (r['kind']=='tracking_frame' and 3000 <= r['timeline_ms'] <= 4000)]
    assert get(meta, gap)['status']=='incomplete_history'
    unpaired = [r for r in rows if r['message_id']!='history-2-start']
    assert get(meta, unpaired)['status']=='incomplete_history'
    for r in rows:
        if r['message_id'].startswith('history-'):
            r['period'] = 2
    assert get(meta, rows)['status']=='insufficient_history'


def test_signed_direction_equality_and_tool_scope():
    meta, rows = scene()
    original = get(meta, rows)
    meta['periods'][0]['attack_direction']['blue'] = 'left'
    for r in rows:
        if r['kind']=='event' and r['payload']['type'] in {'pass_started','pass_resolved'}:
            point = r['payload']['details'].get('start_position', r['payload']['details'].get('end_position'))
            point['x_m'] = 105 - point['x_m']
    assert [p['forward_m'] for p in get(meta, rows)['comparators']] == [10,7,5]
    assert get(meta, rows)['current_forward_m'] == pytest.approx(original['current_forward_m'])
    with pytest.raises(ToolError):
        EvidenceTools(meta,rows,25000,'pass-1').get_recent_pass_context('history-1')
    meta, rows = scene((1,2,original['current_forward_m']))
    assert get(meta,rows)['relation']=='no_comparative_claim'


def test_v3_titles_and_context_are_bound_and_revision_stable_as_clock_advances():
    meta, rows = scene()
    p = build_contextual_package(EvidenceTools(meta,rows,25000,'pass-1'))
    later = build_contextual_package(EvidenceTools(meta,rows,29000,'pass-1'))
    assert p['evidence_revision'] == later['evidence_revision']
    assert PublicationPackage.model_validate(p).schema_version=='3.0.0'
    bad = deepcopy(p);bad['title']='Guaranteed goal'
    with pytest.raises(ValidationError, match='unbound_narrative_title'):
        PublicationPackage.model_validate(bad)
    bad = deepcopy(p);bad['metrics']['context']['comparators'][0]['forward_m']=999
    with pytest.raises(ValidationError, match='context_measurement_mismatch'):
        PublicationPackage.model_validate(bad)
    bad['metrics']['context']['revision']=digest({k:v for k,v in bad['metrics']['context'].items() if k!='revision'})[:16]
    bad['evidence_revision']=digest([bad['metrics']['current_evidence_revision'],bad['metrics']['context']['revision']])[:16]
    for c in bad['claims']: c['evidence_revision']=bad['evidence_revision']
    with pytest.raises(ValidationError):PublicationPackage.model_validate(bad)


def test_angle_and_player_roles_change_the_lead_without_model_calls():
    meta, rows=scene()
    p=build_contextual_package(EvidenceTools(meta,rows,25000,'pass-1'),plan={
        'angle':'reception','simple_claim_ids':['c-forward','c-retain'],
        'detail_claim_ids':['c-bypass','c-retain','c-progress','c-pressure']})
    assert p['variants'][0]['claim_ids'][0]=='c-zone'
    assert 'receives in the' in p['title']
    passer=next(v for v in p['variants'] if v['id']==f'en_simple_{p["metrics"]["passer_id"]}')
    receiver=next(v for v in p['variants'] if v['id']==f'en_simple_{p["metrics"]["receiver_id"]}')
    assert passer['claim_ids'][0]=='c-release'
    assert receiver['claim_ids'][:2]==['c-zone','c-reception']


def test_lookback_lower_boundary_is_inclusive_and_partner_release_can_precede_it():
    meta,rows=scene()
    template=deepcopy(next(r for r in rows if r['kind']=='tracking_frame'))
    for r in rows:
        if r['message_id'].startswith('history-'):
            index=int(r['message_id'].split('-')[1])
            at=7000+index*2000+(1000 if r['payload']['type']=='pass_resolved' else 0)
        else:
            at=r['timeline_ms']+110000
        r.update(timeline_ms=at,period_elapsed_ms=at,available_at_ms=at)
    for at in range(8000,110000,100):
        row=deepcopy(template)
        row.update(message_id=f'continuity-{at}',timeline_ms=at,available_at_ms=at,period_elapsed_ms=at,sequence_no=at)
        rows.append(row)
    context=get(meta,rows,135000)
    assert context['release_ms']==128000 and context['window_start_ms']==8000
    assert context['status']=='available' and [p['pass_id'] for p in context['comparators']]==['history-2','history-1','history-0']
    boundary=next(r for r in rows if r['message_id']=='history-0-end')
    boundary.update(timeline_ms=7999,period_elapsed_ms=7999,available_at_ms=7999)
    context=get(meta,rows,135000)
    assert context['status']=='insufficient_history' and context['sample_count']==2
