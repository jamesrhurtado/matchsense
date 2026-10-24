"""Summarize the raw local polling run without hiding end-boundary limitations."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    path=ROOT/'evals/match-coverage/continuous-play.json';report=json.loads(path.read_text())
    families=defaultdict(lambda:{'attempted':0,'found':0,'target_met':0,'minimum_review_ms':None})
    for session in report['results']:
        for row in session['opportunities']:
            group=families[row['family']];group['attempted']+=1;group['found']+=row['found'];group['target_met']+=row['target_met']
            value=row['review_time_available_ms'];group['minimum_review_ms']=min(value,group['minimum_review_ms']) if group['minimum_review_ms'] is not None else value
    report['family_summary']=dict(families)
    live=[row for session in report['results'] for row in session['opportunities'] if row['evidence_ready_ms']<240000]
    report['live_before_segment_end']={'attempted':len(live),'target_met':sum(row['target_met'] for row in live),'minimum_review_ms':min(row['review_time_available_ms'] for row in live)}
    report['end_boundary_note']='Two 240 s possession snapshots are retained in all-opportunity accounting. The replay clock stops at segment end, so their nominal 15 s review window is not live latency evidence.'
    fingerprints=report['source_sha256']
    report['backend_source_matches_delivery']=all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in fingerprints.items() if name.startswith(('engine/','services/')))
    report['ui_changes_after_timing']=[name for name,sha in fingerprints.items() if name.startswith('apps/') and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha]
    report['ui_scope_note']='Backend HTTP candidate-readiness measurement; browser paint excluded. Any later UI refinements are verified by the final browser suite.'
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'family_summary':report['family_summary'],'live_before_segment_end':report['live_before_segment_end'],'backend_source_matches_delivery':report['backend_source_matches_delivery']},indent=2))
    if not report['backend_source_matches_delivery'] or not live or sum(row['target_met'] for row in live)/len(live)<.9:raise SystemExit(1)

if __name__=='__main__':main()
