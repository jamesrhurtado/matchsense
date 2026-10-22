from copy import deepcopy

from engine.contextual_narrative import build_contextual_package
from engine.core import load_match
from engine.recap import project_recap
from engine.workflow import EvidenceTools


def package():
    m,r=load_match('match-001')
    return build_contextual_package(EvidenceTools(m,r,25000,'pass-1'))


def repeat(p,i,distance=None):
    result=deepcopy(p)
    result.update(id=f'story-repeat-{i}',eligible_from_ms=25000+i*1000,expires_at_ms=55000+i*1000,
                  package_hash=f'hash-{i}')
    if distance is not None:
        next(c for c in result['claims'] if c['id']=='c-forward')['value']=distance
    return result


def test_equivalent_facts_group_without_duplicates_and_later_distinct_fact_survives():
    p=package()
    items=[p,repeat(p,1),repeat(p,2),repeat(p,3,30)]
    recap=project_recap(items,'en',60000)
    assert recap['approved_count']==4 and recap['distinct_count']==2
    assert [m['story_id'] for m in recap['moments']]==['story-pass-1','story-repeat-3']
    assert [m['story_id'] for m in recap['moments'][0]['similar_moments']]==['story-pass-1','story-repeat-1','story-repeat-2']
    assert all(m['archived'] for m in recap['moments'])
    assert project_recap(list(reversed(items)),'en',60000)==recap
    # Projection recomputed from approved inputs: removing a member changes count/hash.
    after=project_recap(items[1:],'en',60000)
    assert after['projection_hash']!=recap['projection_hash']
    assert len(after['moments'][0]['similar_moments'])==2


def test_empty_one_many_focus_and_exact_revision_binding():
    p=package()
    assert project_recap([],'en',60000)['moments']==[]
    assert len(project_recap([p],'en',60000)['moments'])==1
    many=[repeat(p,i,i*10) for i in range(6)]
    assert [m['story_id'] for m in project_recap(many,'en',60000)['moments']]==['story-repeat-3','story-repeat-4','story-repeat-5']
    assert project_recap([p],'en',60000,'amber-01')['moments']==[]
    focused=project_recap([p],'es',60000,p['metrics']['receiver_id'])
    assert 'recibió' in focused['moments'][0]['text']
    changed=deepcopy(p);changed['revision']=2;changed['package_hash']='new-exact-hash'
    assert project_recap([changed],'es',60000)['projection_hash']!=project_recap([p],'es',60000)['projection_hash']
