"""Independent story revision streams, approval isolation, and legacy migration."""
import json
import pytest
from engine.repository import Repository
from engine.cloud_repository import CosmosRepository, RepositoryConflict
from tests.test_cloud import Client


@pytest.fixture(params=['sqlite','cosmos'])
def repo(request,tmp_path):
    return Repository(tmp_path/'stories.db') if request.param=='sqlite' else CosmosRepository(client=Client())


def package(story,revision=1,eligible=1000):
    return {'id':story,'revision':revision,'package_hash':f'{story}:{revision}',
            'workflow_ms':1,'eligible_from_ms':eligible}


def approve(repo,p,key=None):
    return repo.commit_review('s',key or p['id'],p['package_hash'],p['revision'],p['package_hash'],p,
                              'approved',1000,{'id':p['id'],'revision':p['revision']})


def test_story_revisions_and_approvals_are_independent(repo):
    first=package('first',eligible=2000);second=package('second',eligible=1000)
    repo.store_package('s',first,1000,0);approve(repo,first)
    repo.store_package('s',second,1000,0);approve(repo,second)
    assert repo.latest_package('s')==second
    assert [p['id'] for p in repo.list_packages('s')]==['second','first']
    assert repo.decision('s','first')['status']=='approved'
    newer=package('first',2,2000);repo.store_package('s',newer,1000,1)
    assert repo.latest_package('s')==newer
    assert repo.decision('s','first')['status']=='superseded'
    assert repo.decision('s','second')['status']=='approved'
    repo.invalidate('s','first')
    assert repo.decision('s','second')['status']=='approved'
    repo.invalidate('s')
    assert repo.decision('s','second')['status']=='superseded'
    assert all('story_id' in json.loads(row['data']) for row in repo.audit('s'))


def test_review_old_story_does_not_change_latest_story(repo):
    a=package('a');b=package('b')
    repo.store_package('s',a,0,0);repo.store_package('s',b,0,0)
    approve(repo,a)
    assert repo.latest_package('s')==b
    assert repo.decision('s') is None
    assert repo.decision('s','a')['status']=='approved'
    edited=package('a',2)
    repo.commit_review('s','edit','edit',1,a['package_hash'],edited,'ready',0,{},edited=True)
    assert repo.latest_package('s')==edited
    with pytest.raises(RepositoryConflict):approve(repo,a,key='stale')


def test_legacy_story_remains_readable_after_new_story(repo):
    old=package('legacy')
    decision={'session_id':'s','revision':1,'status':'approved','at_ms':0,'package_hash':old['package_hash']}
    if isinstance(repo,Repository):
        with repo.connect() as c:
            c.execute('INSERT INTO packages VALUES (?,?,?)',('s',1,json.dumps(old)))
            c.execute('INSERT INTO editorial VALUES (?,?,?,?,?)',('s',1,'approved',0,old['package_hash']))
    else:
        repo.stories.upsert_item(repo._doc('s','package:1','package',old))
        repo.stories.upsert_item({'id':'current','session_id':'s','revision':1,'package_hash':old['package_hash']})
        repo.stories.upsert_item(repo._doc('s','decision','decision',decision))
    assert repo.latest_package('s')==old
    assert repo.decision('s','legacy')['status']=='approved'
    new=package('new');repo.store_package('s',new,0,0)
    assert repo.latest_package('s','legacy')==old
    assert len(repo.list_packages('s'))==2
    approve(repo,old,key='legacy-review')
    assert repo.latest_package('s')==new
    revised=package('legacy',2);repo.store_package('s',revised,0,1)
    assert repo.latest_package('s','legacy')==revised
    assert repo.decision('s','legacy')['status']=='superseded'


def test_story_identifiers_are_safe_and_idempotency_is_session_wide(repo):
    a=package('a/b:#? 中文');b=package('a_b')
    repo.store_package('s',a,0,0);repo.store_package('s',b,0,0)
    approve(repo,a,key='same')
    with pytest.raises(RepositoryConflict,match='idempotency_key_reused'):
        approve(repo,b,key='same')
    assert repo.latest_package('s',a['id'])==a
    assert repo.latest_package('s',b['id'])==b
    assert repo.decision('s',b['id']) is None


def test_cosmos_story_pointer_race_rolls_back_review():
    repo=CosmosRepository(client=Client());p=package('a')
    repo.store_package('s',p,0,0)
    def race():
        pointer=repo._pointer('s','a')
        repo.stories.upsert_item(pointer)
    repo.stories.before_batch=race
    with pytest.raises(RepositoryConflict,match='stale_revision'):approve(repo,p)
    assert repo.decision('s','a') is None
    assert repo.operation('s','a') is None
    assert len(repo.audit('s'))==1
