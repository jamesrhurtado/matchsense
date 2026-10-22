from concurrent.futures import Future
from copy import deepcopy

import pytest
from engine.repository import Repository
from engine.cloud_repository import CosmosRepository
from engine.core import load_match
from engine.dispositions import record
from services.api import main
from tests.test_cloud import Client
from tests.test_structured_workflow import director,critic
from tests.test_foundry import FakeProvider


@pytest.fixture(params=['sqlite','cosmos'])
def repository(request,tmp_path,monkeypatch):
    repo=Repository(tmp_path/'dispositions.db') if request.param=='sqlite' else CosmosRepository(client=Client())
    monkeypatch.setattr(main,'repo',repo);monkeypatch.setattr(main,'JOBS',{})
    monkeypatch.setattr(main,'FOUNDRY',True);monkeypatch.setattr(main,'STRUCTURED',True)
    monkeypatch.setattr(main,'transport',None)
    return repo


@pytest.mark.parametrize('late_state',['discarded_stale','expired_before_acceptance'])
def test_workflow_completion_is_immutable_when_package_is_later_discarded(repository,monkeypatch,late_state):
    from engine import structured_workflow
    monkeypatch.setattr(structured_workflow,'AgentFrameworkProvider',lambda:FakeProvider([director(),critic()]))
    meta,original=load_match('match-001');rows=deepcopy(original)
    monkeypatch.setattr(main,'load_match',lambda _:(meta,rows))
    pending=[]
    class Worker:
        def submit(self,fn,tools,**kwargs):
            future=Future();pending.append((future,fn,tools,kwargs));return future
    monkeypatch.setattr(main,'WORKERS',Worker())
    session=main.new_session('match-001');sid=session['id']
    assert main.materialize_all(session,25000)==[]
    future,fn,tools,kwargs=pending[0]
    p=fn(tools,**kwargs);future.set_result(p)
    completed=repository.workflow_outcomes(sid)[0]
    assert completed['state']=='produced' and completed['model_usage']['calls']==2
    if late_state=='discarded_stale':
        old=next(r for r in rows if r['kind']=='event' and r['payload']['type']=='pass_resolved')
        correction=deepcopy(old);correction.update(message_id='late-end',supersedes_message_id=old['message_id'],
                                                  revision=2,sequence_no=99999,available_at_ms=26000)
        correction['payload']['details']['end_position']['x_m']+=0.1;rows.append(correction)
        main.materialize_all(session,27000)
    else:
        assert main.materialize_all(session,60000)==[]
    assert repository.workflow_outcomes(sid)[0]==completed
    events=repository.lifecycle_events(sid)
    assert any(e['kind']=='disposition' and e['state']==late_state and e['run_id']==completed['run_id'] for e in events)
    assert repository.latest_package(sid) is None
    # Re-reading does not double-count the disposition.
    main.materialize_all(session,27000 if late_state=='discarded_stale' else 60000)
    assert len([e for e in repository.lifecycle_events(sid) if e['kind']=='disposition' and e['run_id']==completed['run_id']])==1


def test_append_only_events_deduplicate_and_capacity_or_expiry_cannot_disappear(repository,monkeypatch):
    sid=main.new_session('match-001')['id'];s=repository.get_session(sid)
    event=record(repository,sid,'opportunity',['id'],story_id='story-pass-1',state='detected')
    assert record(repository,sid,'opportunity',['id'],story_id='story-pass-1',state='replacement')==event
    monkeypatch.setattr(main,'JOBS',{('other',str(i),'revision'):Future() for i in range(4)})
    assert main.materialize_all(s,25000)==[]
    assert any(e.get('state')=='capacity_deferred' for e in repository.lifecycle_events(sid))
    assert main.materialize_all(s,60000)==[]
    assert any(e.get('state')=='expired_unscheduled' for e in repository.lifecycle_events(sid))
    assert repository.workflow_outcomes(sid)==[]
