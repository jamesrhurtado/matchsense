"""Export observation-only paired history replays; old 168-case suite is untouched.

Offline schedules and expectations stay in provenance/evaluation-only folders.
This reuses the trajectory backbone and is developer discovery, not final QA.
"""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path

from simulator.scenarios import Case, Parent
from simulator.suite import generate_case, serialize

ROOT=Path(__file__).resolve().parents[1]


def build_replays():
    result=[]
    for name,distances in [('a',[8,12,16,30,22]),('b',[32,34,36,30,22])]:
        case=Case(f'context-replay-{name}',Parent('context-shared-current','discovery',26,30,30,False,'blue',12000,9107),'long_session')
        schedule=[{'release_ms':12000+i*25000,'forward_m':value} for i,value in enumerate(distances)]
        data=generate_case(case,passage_schedule=schedule)
        reference={'split':'developer-visible discovery','shared_backbone':'suite-v2-trajectory-backbone',
                   'paired_current_pass':'pass-4','expected_comparator_ids':['pass-3','pass-2','pass-1'],
                   'expected_forward_m':list(reversed(distances[:3])),
                   'relation':'greater_than_each' if name=='a' else 'no_comparative_claim',
                   'football_review':'pending','independent_final':'not a final case',
                   'schedule':schedule,'duration_ms':150000}
        result.append((data,reference,f'Previous-pass history {name.upper()} · 5 moments · 2.5 min'))
    return result


def main():
    catalog_path=ROOT/'data/runtime/catalog.json'
    catalog=json.loads(catalog_path.read_text())
    manifest=[]
    for data,reference,label in build_replays():
        mid=data.metadata['match_id'];folder=ROOT/'data/runtime'/mid;folder.mkdir(exist_ok=True)
        metadata=json.dumps(data.metadata,indent=2)+'\n'
        raw=serialize(data.observations).encode();compressed=gzip.compress(raw,mtime=0)
        (folder/'match.json').write_text(metadata)
        (folder/'stream.jsonl.gz').write_bytes(compressed)
        reference_folder=ROOT/'data/evaluation-only/context';reference_folder.mkdir(exist_ok=True)
        (reference_folder/f'{mid}.json').write_text(json.dumps(reference,indent=2)+'\n')
        row={'match_id':mid,'label':label,'duration_ms':150000,'synthetic':True}
        catalog=[r for r in catalog if r['match_id']!=mid]+[row]
        manifest.append({'match_id':mid,'compressed_sha256':hashlib.sha256(compressed).hexdigest(),
                         'observations_sha256':hashlib.sha256(raw).hexdigest(),
                         'metadata_sha256':hashlib.sha256(metadata.encode()).hexdigest()})
    catalog_path.write_text(json.dumps(catalog,indent=2)+'\n')
    (ROOT/'data/provenance/context-replays.json').write_text(json.dumps({'generator':'simulator.context_replays',
        'status':'developer discovery; paired histories share one current-play backbone; football review pending',
        'cases':manifest},indent=2)+'\n')
    print('Exported two paired context replays; existing regression inputs unchanged.')


if __name__=='__main__':main()
