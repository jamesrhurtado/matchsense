"""Independent hand-reference checkpoints; no production-derived expected values."""
from copy import deepcopy
import json
from pathlib import Path
from engine.core import load_match
from engine.contracts import OBSERVATION
from engine.match_state import match_state
from engine.event_metrics import event_metrics, possession_window
from simulator.validate import validate_feed

ROOT=Path(__file__).resolve().parents[1]


def evaluate():
    meta=load_match('match-001')[0];results=[]
    reference=json.loads((ROOT/'evals/match-coverage/cases.json').read_text())
    for case in reference['cases']:
        rows=[]
        for i,spec in enumerate(case.get('events',[])):
            t,kind,details,*rest=spec
            team,player,ready,revision,prior=(rest+[None]*5)[:5]
            rows.append({'schema_version':'1.0.0','match_id':meta['match_id'],'message_id':f'case-{i}', 'sequence_no':i,
                         'timeline_ms':t,'period':1,'period_elapsed_ms':t,'available_at_ms':ready if ready is not None else t,
                         'revision':revision or 1,'supersedes_message_id':f'case-{prior}' if prior is not None else None,
                         'kind':'event','payload':{'event_id':f'e-{prior if prior is not None else i}','type':kind,'team_id':team or 'blue','player_id':player,'possession_id':None,'details':details}})
        f=case.get('frames')
        if f:
            for t in range(f.get('start',0),f['end']+1,f['step']):
                if f.get('omit') and f['omit'][0]<=t<f['omit'][1]:continue
                if f.get('thin_blue') and t<f['blue_until'] and t%200==100:continue
                status='out_of_play' if t<f.get('dead_until',0) else 'loose' if t<f.get('loose_until',0) else 'in_flight'
                team='blue' if t<f.get('blue_until',10**10) else 'amber'
                rows.append({'schema_version':'1.0.0','match_id':meta['match_id'],'message_id':f'f-{t}','sequence_no':t+100,
                             'timeline_ms':t,'period':1,'period_elapsed_ms':t,'available_at_ms':t,'revision':1,'supersedes_message_id':None,
                             'kind':'tracking_frame','payload':{'frame_id':f'f-{t}','players':[],'missing_player_ids':[],'ball':None,'ball_status':status,
                             'controlling_player_id':None,'possession_team_id':team if status=='in_flight' else None}})
        if case.get('duplicate'):rows+=deepcopy(rows)
        if case.get('reverse'):rows.reverse()
        for row in rows:OBSERVATION.validate_python(row)
        ms=event_metrics(meta,rows,case['cutoff']);state=match_state(meta,rows,case['cutoff'])
        families={family:[m for m in ms if m['family']==family] for family in ['goal','shot','recovery']}
        actual={'score':state['score'],**{family+'_count':len(values) for family,values in families.items()}}
        for family,role in [('goal','scorer'),('shot','shooter'),('recovery','recovering_player')]:
            if families[family]:actual[role]=families[family][0]['participants'][role]
        if families['shot']:actual['shot_outcome']=families['shot'][0]['facts']['outcome']
        if families['recovery']:actual.update(control_kind=families['recovery'][0]['facts']['kind'],sustained=families['recovery'][0]['facts']['sustained'])
        if f:
            w=possession_window(meta,rows,case['cutoff'],f['end'])
            actual.update({k:w[k] for k in ['assigned_ms','unknown_ms','dead_ms','loose_ms']})
            actual.update(blue_ms=w['team_ms']['blue'],amber_ms=w['team_ms']['amber'],has_percentages=w['percentages'] is not None)
        failures={k:{'expected':v,'actual':actual.get(k)} for k,v in case['expected'].items() if actual.get(k)!=v}
        results.append({'id':case['id'],'passed':not failures,'failures':failures})
    physical=[{'match_id':mid,**validate_feed(*load_match(mid))} for mid in ['match-0c0a000000000001','match-0c0a000000000002']]
    return {'authorship':reference['authorship'],'model_calls':0,'checkpoints':len(results),'passed':sum(r['passed'] for r in results),'results':results,'fixture_validation':physical}


def main():
    report=evaluate();folder=ROOT/'evals/match-coverage'
    (folder/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"Mixed-event independent references: {report['passed']}/{report['checkpoints']}; 2 physical/feed checks; zero model calls.")
    if report['passed']!=report['checkpoints']:raise SystemExit(1)

if __name__=='__main__':main()
