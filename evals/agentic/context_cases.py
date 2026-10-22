"""Authored history challenges around a shared present-play recording.

Developer-visible discovery only. Eight variants are repeated measurements of one
current play, not eight independent football parents. References are handwritten
here and never cross RuntimeInput or enter runtime images.
"""
from copy import deepcopy
from engine.core import load_match
from .dataset import EvaluationCase, RuntimeInput


def context_cases():
    definitions = [
        ('history-contrast', (5,7,10), 'available', ['h2','h1','h0'], 'greater_than_each'),
        ('history-ordinary', (20,21,22), 'available', ['h2','h1','h0'], 'no_comparative_claim'),
        ('history-mixed', (5,25,10), 'available', ['h2','h1','h0'], 'no_comparative_claim'),
        ('history-backward', (-5,0,10), 'available', ['h2','h1','h0'], 'greater_than_each'),
        ('history-short', (5,7), 'insufficient_history', ['h1','h0'], 'no_comparative_claim'),
        ('history-missing-start', (5,7,10), 'incomplete_history', ['h1','h0'], 'no_comparative_claim'),
        ('history-tracking-gap', (5,7,10), 'incomplete_history', ['h2','h1','h0'], 'no_comparative_claim'),
        ('history-corrected', (5,7,10), 'available', ['h2','h1','h0'], 'no_comparative_claim'),
    ]
    cases=[]
    for name,distances,status,ids,relation in definitions:
        metadata,original=load_match('match-001')
        metadata,rows=deepcopy(metadata),deepcopy(original)
        start=next(r for r in rows if r['kind']=='event' and r['payload']['type']=='pass_started')
        end=next(r for r in rows if r['kind']=='event' and r['payload']['type']=='pass_resolved')
        for i,distance in enumerate(distances):
            for source,kind,at in [(start,'start',1000+i*2000),(end,'end',2000+i*2000)]:
                row=deepcopy(source)
                row.update(message_id=f'h{i}-{kind}',timeline_ms=at,available_at_ms=at,
                           period_elapsed_ms=at,sequence_no=10000+i*2+(kind=='end'))
                row['payload']['event_id']=row['message_id']
                row['payload']['details']['pass_id']=f'h{i}'
                if kind=='start':row['payload']['details']['start_position']={'x_m':20,'y_m':30}
                else:row['payload']['details']['end_position']={'x_m':20+distance,'y_m':30}
                rows.append(row)
        if name=='history-missing-start':rows=[r for r in rows if r['message_id']!='h2-start']
        if name=='history-tracking-gap':rows=[r for r in rows if not(r['kind']=='tracking_frame' and 3000<=r['timeline_ms']<=4000)]
        if name=='history-corrected':
            old=next(r for r in rows if r['message_id']=='h2-end')
            correction=deepcopy(old)
            correction.update(message_id='corrected-h2',supersedes_message_id=old['message_id'],
                              revision=2,available_at_ms=24000,sequence_no=99999)
            correction['payload']['details']['end_position']['x_m']=60
            rows.append(correction)
        visible=[r for r in rows if r['timeline_ms']<=25000 and r['available_at_ms']<=25000]
        cases.append(EvaluationCase(name,'authored-history/shared-current-match-001',
                     'Authored previous-pass population: '+name.replace('history-',''),
                     RuntimeInput(metadata,visible,25000,'pass-1'),
                     {'expected_story':True,'context_status':status,'comparator_ids':ids,'relation':relation,
                      'human_review':'pending','football_realism_review':'pending',
                      'expected_narrative':None,'forbidden_claims':['best pass','chance created','tactical superiority']}))
    return cases
