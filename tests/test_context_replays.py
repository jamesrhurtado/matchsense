from engine.contextual_narrative import build_contextual_package
from engine.workflow import EvidenceTools
from simulator.context_replays import build_replays
from simulator.validate import validate,validate_feed
from engine.contracts import OBSERVATION


def test_paired_replays_are_feed_valid_have_five_moments_and_same_present_geometry():
    a,b=build_replays()
    packages=[]
    for data,reference,_ in [a,b]:
        assert validate(data.metadata,data.clean)['frames']==1501
        assert validate_feed(data.metadata,data.observations)['duration_ms']==150000
        for row in data.observations:OBSERVATION.validate_python(row)
        for i in range(1,6):
            assert build_contextual_package(EvidenceTools(data.metadata,data.observations,120000,f'pass-{i}'))
        p=build_contextual_package(EvidenceTools(data.metadata,data.observations,95000,'pass-4'))
        assert [r['pass_id'] for r in p['metrics']['context']['comparators']]==reference['expected_comparator_ids']
        assert [r['forward_m'] for r in p['metrics']['context']['comparators']]==reference['expected_forward_m']
        assert p['metrics']['context']['relation']==reference['relation']
        packages.append(p)
    assert packages[0]['metrics']['current_evidence_revision']!=packages[1]['metrics']['current_evidence_revision'] # Match IDs differ, current payloads do not.
    for key in ['forward_pass_m','pass_start','pass_end','progression_m','passer_id','receiver_id']:
        assert packages[0]['metrics'][key]==packages[1]['metrics'][key]
    def present(data):
        return [m['payload'] for m in data.observations if 85000<=m['timeline_ms']<=91200]
    assert present(a[0])==present(b[0])
