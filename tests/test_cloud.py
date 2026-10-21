"""Cloud transaction and transport invariants without paid network dependencies."""
from copy import deepcopy
import json
from types import SimpleNamespace
import pytest
from engine.cloud_repository import CosmosRepository, RepositoryConflict
from engine.repository import Repository
from engine.core import load_match, available
from engine.transport import EventHubTransport


class HTTPError(Exception):
    def __init__(self, status):
        self.status_code = status


class Container:
    def __init__(self):
        self.items = {}
        self.version = 0
        self.before_batch = None

    def read_item(self, item, partition_key):
        if (partition_key,item) not in self.items:
            raise HTTPError(404)
        return deepcopy(self.items[(partition_key,item)])

    def create_item(self, body):
        key = body['session_id'],body['id']
        if key in self.items:
            raise HTTPError(409)
        return self.upsert_item(body)

    def upsert_item(self, body):
        self.version += 1
        body = deepcopy(body)
        body['_etag'] = str(self.version)
        self.items[(body['session_id'],body['id'])] = body
        return body

    def query_items(self, query, partition_key=None, **kwargs):
        rows = [deepcopy(d) for (sid,_),d in self.items.items() if partition_key is None or sid == partition_key]
        kind = next((k for k in ('session','audit','observation') if f'"{k}"' in query),None)
        rows = [d for d in rows if d.get('type') == kind]
        parameters=kwargs.get('parameters',[])
        if parameters:
            wanted=parameters[0]['value']
            rows=[d for d in rows if d['id'] in wanted]
        key = 'created_at' if 'created_at' in query else 'sequence_no'
        return sorted(rows,key=lambda d:d.get(key,0))

    def execute_item_batch(self, batch_operations, partition_key):
        if self.before_batch:
            callback,self.before_batch = self.before_batch,None
            callback()
        original = deepcopy(self.items)
        try:
            for method,args,*rest in batch_operations:
                options = rest[0] if rest else {}
                if method == 'replace':
                    key,body = args
                    old = self.read_item(key,partition_key)
                    if old['_etag'] != options['if_match_etag']:
                        raise HTTPError(412)
                    self.upsert_item(body)
                elif method == 'create':
                    self.create_item(args[0])
                elif method == 'upsert':
                    self.upsert_item(args[0])
                else:
                    raise AssertionError(method)
        except Exception:
            self.items = original
            raise
        return []


class Client:
    def __init__(self):
        self.containers = {}
    def get_database_client(self,name):
        return self
    def get_container_client(self,name):
        return self.containers.setdefault(name,Container())


@pytest.fixture(params=['sqlite','cosmos'])
def repo(request,tmp_path):
    return Repository(tmp_path/'test.db') if request.param == 'sqlite' else CosmosRepository(client=Client())


def package(revision=1):
    return {'revision':revision,'package_hash':str(revision)*64,'workflow_ms':1,'id':'story'}


def review(repo,key='approval-1',request_hash='request',expected=1,edited=False):
    p = package(expected+1 if edited else expected)
    return repo.commit_review('session',key,request_hash,expected,str(expected)*64,p,
        'ready' if edited else 'approved',22000,{'revision':p['revision']},edited=edited)


def test_publication_transaction_and_idempotency(repo):
    repo.store_package('session',package(),22000,0)
    assert review(repo) == {'revision':1}
    assert review(repo) == {'revision':1}
    assert len(repo.audit('session')) == 2
    with pytest.raises(RepositoryConflict,match='idempotency_key_reused'):
        review(repo,request_hash='changed')
    review(repo,key='edit-1',edited=True)
    assert repo.latest_package('session')['revision'] == 2
    assert repo.decision('session')['status'] == 'ready'
    with pytest.raises(RepositoryConflict,match='stale_revision'):
        review(repo,key='stale')
    assert len(repo.audit('session')) == 3
    repo.invalidate('session')
    assert repo.decision('session')['status'] == 'superseded'


def test_package_is_immutable(repo):
    repo.store_package('session',package(),22000,0)
    with pytest.raises(RepositoryConflict,match='stale_revision'):
        repo.store_package('session',package(),22000,0)
    assert repo.latest_package('session') == package()


def test_cosmos_etag_conflict_rolls_back_entire_review():
    repo = CosmosRepository(client=Client())
    repo.store_package('session',package(),22000,0)
    def competing_change():
        old=repo.stories.read_item('current','session')
        repo.stories.upsert_item(old)
    repo.stories.before_batch = competing_change
    with pytest.raises(RepositoryConflict,match='stale_revision'):
        review(repo)
    assert repo.decision('session') is None
    assert repo.operation('session','approval-1') is None
    assert len(repo.audit('session')) == 1


def test_durable_dedup_and_conflicting_ids(repo):
    _,messages=load_match('match-001')
    message=messages[0]
    assert repo.append_observation('session',message)
    assert not repo.append_observation('session',deepcopy(message))
    altered=deepcopy(message)
    altered['available_at_ms']+=1
    with pytest.raises(RepositoryConflict,match='observation_id_reused'):
        repo.append_observation('session',altered)
    assert repo.read_observations('session') == [message]


def transport(repo):
    repo.save_session({'id':'session','generation':1,'match_id':'match-001'})
    return EventHubTransport(repo,producer=object(),consumer=object())


def envelope(message,generation=1):
    return {'session_id':'session','match_id':'match-001','generation':generation,'observation':message}


def test_consumer_restart_future_cutoff_and_generation(repo):
    t=transport(repo)
    _,messages=load_match('match-001')
    m=messages[50]
    t.accept(envelope(m))
    assert t.messages(repo.get_session('session'),m['available_at_ms']-1) == []
    restarted=EventHubTransport(repo,producer=object(),consumer=object())
    assert restarted.messages(repo.get_session('session'),m['available_at_ms']) == [m]
    assert not restarted.accept(envelope(m))
    with pytest.raises(ValueError,match='generation_mismatch'):
        t.accept(envelope(m,generation=2))


def test_failed_persistence_cannot_be_checkpointed_past(repo):
    t=transport(repo)
    _,messages=load_match('match-001')
    checkpoint=[]
    context=SimpleNamespace(partition_id='0',update_checkpoint=lambda e:checkpoint.append(e))
    def event(m):
        return SimpleNamespace(body_as_str=lambda **kw:json.dumps(envelope(m)))
    first,second=event(messages[0]),event(messages[1])
    real=t.accept
    def fail(_):
        raise OSError('simulated_cosmos_unavailable')
    t.accept=fail
    with pytest.raises(OSError):
        t.on_event(context,first)
    assert checkpoint == []
    t.accept=real
    t._checkpoint_counts['0']['at']=0
    t.on_event(context,second)
    assert checkpoint == [second]
    assert repo.read_observations('session') == messages[:2]


def test_delivered_correction_supersedes_original(repo):
    t=transport(repo)
    _,messages=load_match('match-001')
    original=messages[0]
    corrected=deepcopy(original)
    corrected.update(message_id='corrected',revision=2,supersedes_message_id=original['message_id'],available_at_ms=1000,sequence_no=9000)
    t.accept(envelope(corrected))
    t.accept(envelope(original))
    session=repo.get_session('session')
    assert t.messages(session,999) == [original]
    assert t.messages(session,1000) == [corrected]


def test_sender_crash_after_send_retries_without_losing_delayed_observation(repo,monkeypatch):
    import sys
    import engine.transport as module
    class EventData:
        def __init__(self,body): self.body=body
    monkeypatch.setitem(sys.modules,'azure.eventhub',SimpleNamespace(EventData=EventData))
    _,messages=load_match('match-001')
    delayed=deepcopy(messages[0]);delayed['available_at_ms']=2000
    earlier=messages[1]
    monkeypatch.setattr(module,'load_match',lambda _:({},[delayed,earlier]))
    class Batch:
        def __init__(self):self.events=[]
        def add(self,event):self.events.append(event)
    class Producer:
        def __init__(self):self.delivered=[];self.fail=True
        def create_batch(self,**kwargs):return Batch()
        def send_batch(self,batch):
            self.delivered.extend(batch.events)
            if self.fail:
                self.fail=False
                raise OSError('connection_lost_after_acceptance')
    publisher=Producer()
    repo.save_session({'id':'session','generation':1,'match_id':'match-001','clock_ms':1000,'running':False,'speed':1,'updated_at':0})
    t=EventHubTransport(repo,producer=publisher,consumer=object())
    with pytest.raises(OSError):t.publish_session(repo.get_session('session'))
    assert repo.transport_cursor('session') == -1
    t.publish_session(repo.get_session('session'))
    assert repo.transport_cursor('session') == 0
    session=repo.get_session('session');session['clock_ms']=2000;repo.save_session(session)
    t.publish_session(session)
    for event in publisher.delivered:t.accept(json.loads(event.body))
    assert len(repo.read_observations('session')) == 2
    assert {m['message_id'] for m in t.messages(session,2000)} == {delayed['message_id'],earlier['message_id']}


def test_invalidation_changes_etag_and_blocks_racing_approval():
    repo=CosmosRepository(client=Client())
    repo.store_package('session',package(),22000,0)
    review(repo)
    repo.stories.before_batch=lambda:repo.invalidate('session')
    with pytest.raises(RepositoryConflict,match='stale_revision'):
        review(repo,key='racing-approval')
    assert repo.decision('session')['status'] == 'superseded'
    assert repo.operation('session','racing-approval') is None


def test_idle_consumer_does_not_clear_publisher_failure(repo):
    t=transport(repo)
    context=SimpleNamespace(partition_id='0',update_checkpoint=lambda _:None)
    t.publisher_error='OSError: sender is unavailable'
    t.consumer_error='transient receive failure'
    t.on_event(context,None)
    assert t.consumer_error is None
    assert t.diagnostics()['last_error'] == 'publisher: OSError: sender is unavailable'
    t._on_error(context,RuntimeError('receiver is unavailable'))
    assert 'publisher:' in t.last_error and 'consumer:' in t.last_error
    t.publisher_error=None
    assert t.last_error == 'consumer: RuntimeError: receiver is unavailable'


def test_cache_reconciles_rows_checkpointed_by_another_host(repo,monkeypatch):
    import engine.transport as module
    now=[100.0]
    monkeypatch.setattr(module.time,'monotonic',lambda:now[0])
    t=transport(repo)
    external=Repository(repo.path) if isinstance(repo,Repository) else CosmosRepository(client=repo.client)
    _,messages=load_match('match-001')
    initial,later,future=messages[0],messages[1],messages[20]
    external.append_observation('session',initial)
    session=repo.get_session('session')
    cutoff=later['available_at_ms']
    assert t.messages(session,cutoff) == [initial]
    # A different ACA revision owns the partition and checkpoints these writes;
    # this process gets no local consumer callback for either observation.
    external.append_observation('session',later)
    external.append_observation('session',future)
    now[0]=101.0
    assert t.messages(session,cutoff) == [initial]
    now[0]=102.1
    assert t.messages(session,cutoff) == [initial,later]
    assert future['message_id'] in t.cache['session']
    # Refresh merges durable arrivals without weakening the replay cutoff.
    assert t.messages(session,future['available_at_ms']) == [initial,later,future]


def test_bulk_observations_are_atomic_and_duplicate_safe(repo):
    _,messages=load_match('match-001')
    rows=messages[:100]
    assert repo.append_observations('session',rows) == 100
    assert repo.append_observations('session',rows) == 0
    changed=deepcopy(rows[0]);changed['available_at_ms']+=1
    with pytest.raises(RepositoryConflict,match='observation_id_reused'):
        repo.append_observations('session',[messages[100],changed])
    assert len(repo.read_observations('session')) == 100


def test_bulk_cosmos_retries_concurrent_exact_creation():
    repo=CosmosRepository(client=Client())
    _,messages=load_match('match-001')
    first,second=messages[:2]
    def competing_write():
        doc=repo._doc('session','observation:'+first['message_id'],'observation',first)
        doc['sequence_no']=first['sequence_no']
        repo.observations.create_item(doc)
    repo.observations.before_batch=competing_write
    assert repo.append_observations('session',[first,second]) == 1
    assert repo.read_observations('session') == [first,second]


def test_batch_consumer_caches_immutable_session_and_checkpoints_after_durability(repo,monkeypatch):
    t=transport(repo)
    _,messages=load_match('match-001')
    calls=[]
    original=repo.get_session
    def counted(sid):
        calls.append(sid)
        return original(sid)
    monkeypatch.setattr(repo,'get_session',counted)
    events=[SimpleNamespace(body_as_str=lambda m=m,**kw:json.dumps(envelope(m))) for m in messages[:100]]
    checkpoints=[]
    context=SimpleNamespace(partition_id='0',update_checkpoint=lambda event:checkpoints.append((event,len(repo.read_observations('session')))))
    t.on_event_batch(context,events)
    assert calls == ['session']
    assert checkpoints == [(events[-1],100)]
    assert t.received == 100
    t.on_event_batch(context,events)
    assert calls == ['session']
    assert t.received == 100


def test_batch_consumer_retries_failed_batch_before_checkpoint(repo,monkeypatch):
    t=transport(repo)
    _,messages=load_match('match-001')
    events=[SimpleNamespace(body_as_str=lambda m=m,**kw:json.dumps(envelope(m))) for m in messages[:3]]
    checkpoints=[]
    context=SimpleNamespace(partition_id='0',update_checkpoint=lambda e:checkpoints.append(e))
    original=repo.append_observations
    def fail(*args):raise OSError('database_unavailable')
    monkeypatch.setattr(repo,'append_observations',fail)
    with pytest.raises(OSError):t.on_event_batch(context,events[:2])
    assert checkpoints == []
    monkeypatch.setattr(repo,'append_observations',original)
    t.on_event_batch(context,events[2:])
    assert checkpoints == [events[-1]]
    assert repo.read_observations('session') == messages[:3]
