from __future__ import annotations
import asyncio
import json
import os
import secrets
import threading
import time
import uuid
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import logging
from pydantic import BaseModel, ConfigDict, Field
from engine.core import available, digest, load_match, metric, visual_snapshot
from engine.repository import Repository
from engine.workflow import EvidenceTools, run_workflow

ROOT=Path(__file__).resolve().parents[2]
from engine.cloud_repository import CosmosRepository, RepositoryConflict
CLOUD=os.getenv('WHY_NOW_ENVIRONMENT')=='azure'
FOUNDRY=os.getenv('WHY_NOW_MODEL_MODE','template')=='foundry'
repo=CosmosRepository() if os.getenv('WHY_NOW_COSMOS_ENDPOINT') else Repository(os.getenv('WHY_NOW_DB',str(ROOT/'why_now.db')))
transport=None
if os.getenv('WHY_NOW_EVENTHUB_NAMESPACE'):
    from engine.transport import EventHubTransport
    transport=EventHubTransport(repo)
WORKERS=ThreadPoolExecutor(max_workers=2,thread_name_prefix='story')
JOBS={}
logger=logging.getLogger('whynow')

def workflow(tools,**kwargs):
    if FOUNDRY:
        from engine.foundry_workflow import run_foundry_workflow
        from opentelemetry import trace
        with trace.get_tracer('whynow').start_as_current_span('story.workflow',attributes={'source.cutoff_ms':tools.cutoff_ms,'workflow.revision':kwargs.get('revision',1)}):
            return run_foundry_workflow(tools,**kwargs)
    return run_workflow(tools,**kwargs)

def inputs(session,at):
    meta,messages=load_match(session['match_id'])
    return meta,transport.messages(session,at) if transport else messages

def runtime_mode():return 'Microsoft Agent Framework + Azure OpenAI' if FOUNDRY else 'local deterministic template'

@asynccontextmanager
async def lifespan(app):
    if CLOUD and (not os.getenv('WHY_NOW_PRODUCER_TOKEN') or TOKEN=='local-demo-producer' or len(TOKEN)<24):
        raise RuntimeError('Cloud deployment requires a private producer key of at least 24 characters')
    if transport:transport.start()
    yield
    if transport:transport.close()

TOKEN=os.getenv('WHY_NOW_PRODUCER_TOKEN','local-demo-producer')
LOCK=threading.RLock()
app=FastAPI(title='WHY/NOW',version='0.2.0',lifespan=lifespan)
if os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING'):
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    configure_azure_monitor(logger_name='whynow',enable_live_metrics=False)
    FastAPIInstrumentor.instrument_app(app)

app.add_middleware(CORSMiddleware,allow_origins=os.getenv('WHY_NOW_ORIGINS','http://localhost:3000,http://127.0.0.1:3000').split(','),allow_methods=['GET','POST'],allow_headers=['Content-Type','X-Producer-Token','Last-Event-ID'])

class Body(BaseModel): model_config=ConfigDict(extra='forbid')
class Create(Body): match_id:Literal['match-001','match-002','match-003']='match-001'
class Control(Body):
    action:Literal['start','pause','speed','reset']
    speed:float|None=Field(default=None,ge=.25,le=8,allow_inf_nan=False)
class Review(Body):
    action:Literal['approve','suppress','retract','edit']
    expected_revision:int=Field(ge=1)
    package_hash:str=Field(min_length=64,max_length=64)
    idempotency_key:str=Field(min_length=8,max_length=100)
    text:str|None=Field(default=None,max_length=1000)
class RecapRequest(Body):
    through_ms:int|None=Field(default=None,ge=0,le=60000)
    language:Literal['en','es']='en'


def fail(status,code): raise HTTPException(status,detail={'code':code})
def require(token):
    if not token or not secrets.compare_digest(token,TOKEN):fail(401,'producer_auth_required')
def producer(token):
    if token is None:return False
    require(token);return True

def get_session(sid):
    s=repo.get_session(sid)
    if not s:fail(404,'unknown_session')
    return s

def clock(s):
    elapsed=max(0,time.time()-s['updated_at'])*s['speed']*1000 if s['running'] else 0
    return min(60000,int(s['clock_ms']+elapsed))

def new_session(match_id):
    s={'id':str(uuid.uuid4()),'match_id':match_id,'clock_ms':0,'running':False,'speed':1,'updated_at':time.time(),'generation':1,'control_revision':1}
    repo.save_session(s);return s

def materialize(s,at):
    meta,messages=inputs(s,at); old=repo.latest_package(s['id']); m=metric(messages,at,meta)
    if not m or not m['eligible']:
        if old:repo.invalidate(s['id'])
        return None
    if old and old['evidence_revision']==m['evidence_revision']:return old
    if old:repo.invalidate(s['id'])
    revision=old['revision']+1 if old else 1
    if not FOUNDRY:
        package=workflow(EvidenceTools(meta,messages,at),revision=revision)
        if package:repo.store_package(s['id'],package,at,expected_revision=revision-1)
        return package
    key=(s['id'],m['evidence_revision'])
    future=JOBS.get(key)
    if future is None:
        if sum(not f.done() for f in JOBS.values())>=4:return None
        future=WORKERS.submit(workflow,EvidenceTools(meta,messages,at),revision=revision)
        JOBS[key]=future
        return None
    if not future.done():return None
    try:
        package=future.result()
        if package:
            repo.store_package(s['id'],package,at,expected_revision=revision-1)
            logger.info('workflow_complete session=%s revision=%s mode=%s calls=%s',s['id'],revision,package['mode'],package.get('model_calls',package.get('model_usage',{})))
        return package
    except RepositoryConflict:
        return repo.latest_package(s['id'])
    except Exception:
        logger.exception('workflow_failed session=%s',s['id'])
        return None


def publication(s,package,at):
    if not package:return 'none',None
    decision=repo.decision(s['id'])
    status=decision['status'] if decision and decision['revision']==package['revision'] and decision['package_hash']==package['package_hash'] else 'ready'
    if at>=package['expires_at_ms'] and status in ('approved','ready'):status='expired'
    published=bool(decision and decision['status']=='approved' and decision['revision']==package['revision'] and decision['package_hash']==package['package_hash'] and decision['at_ms']<=at)
    return status,package if published else None

def safe_story(package,status):
    if not package:return None
    return {k:package[k] for k in ['id','revision','title','evidence_revision','eligible_from_ms','expires_at_ms']}|{'status':status}

def snapshot_data(sid,is_producer=False):
    with LOCK:
        s=get_session(sid);at=clock(s);meta,messages=inputs(s,at); package=materialize(s,at);status,published=publication(s,package,at)
        current=package if is_producer else published
        view=visual_snapshot(messages,at)
        latest=repo.latest_package(sid)
        revision=latest['revision'] if latest else 0
        audit=repo.audit(sid)
        visible_story=safe_story(current,status)
        if visible_story and is_producer:visible_story['package_hash']=current['package_hash']
        return {'session_id':sid,'match_id':s['match_id'],'clock_ms':at,'duration_ms':60000,'running':s['running'] and at<60000,'speed':s['speed'],'synthetic':True,'score':meta['initial_state']['score'],'teams':meta['teams'],'players':meta['players'],**view,'story':visible_story,'story_status':status if is_producer or published else 'waiting','overlay':next(v['text'] for v in published['variants'] if v['id']=='en_simple_general') if published and status=='approved' else None,'mode':current['mode'] if current else runtime_mode(),'workflow_pending':any(k[0]==sid and not f.done() for k,f in JOBS.items()),'cursor':len(audit)*1000000+s['control_revision']*100000+at,'generation':s['generation']}

def authorized_package(sid,story_id,token=None):
    s=get_session(sid);at=clock(s); p=materialize(s,at)
    if not p or story_id!=p['id']:fail(404,'story_unavailable')
    status,published=publication(s,p,at)
    if not producer(token) and not published:fail(404,'story_unavailable')
    return s,at,p,status

@app.get('/api/health')
def health():return {'ok':True,'mode':runtime_mode(),'azure_deployed':CLOUD,'version':'0.2.0'}

@app.get('/api/ready')
def ready():
    if CLOUD:
        repo.list_sessions()
        if transport and transport.diagnostics().get('last_error'):fail(503,'transport_not_ready')
    return {'ok':True,'persistence':'cosmos' if isinstance(repo,CosmosRepository) else 'sqlite','transport':'eventhubs' if transport else 'local','model':runtime_mode()}


@app.post('/api/replay-sessions')
def create(body:Create,x_producer_token:str|None=Header(None)):
    require(x_producer_token)
    with LOCK:s=new_session(body.match_id)
    return {'session_id':s['id'],'match_id':s['match_id']}

@app.post('/api/replay-sessions/{sid}/control')
def control(sid:str,body:Control,x_producer_token:str|None=Header(None)):
    require(x_producer_token)
    with LOCK:
        s=get_session(sid)
        if body.action=='reset':
            fresh=new_session(s['match_id']);return {'session_id':fresh['id'],'reset_from':sid}
        at=clock(s);s['clock_ms']=at;s['updated_at']=time.time();s['control_revision']+=1
        if body.action=='start':s['running']=True
        elif body.action=='pause':s['running']=False
        if body.speed is not None:s['speed']=body.speed
        repo.save_session(s)
        return {'session_id':sid,'clock_ms':at,'running':s['running'],'speed':s['speed']}

@app.get('/api/replay-sessions/{sid}/snapshot')
def snapshot(sid:str,x_producer_token:str|None=Header(None)):
    return snapshot_data(sid,producer(x_producer_token))

@app.get('/api/replay-sessions/{sid}/stream')
async def stream(sid:str,request:Request,last_event_id:str|None=Header(None)):
    get_session(sid)
    async def events():
        previous=None; ticks=0
        while not await request.is_disconnected():
            data=await asyncio.to_thread(snapshot_data,sid,False)
            signature=digest(data)
            if signature!=previous:
                kind='resync' if previous is None else 'state_update'
                yield f'id: {data["cursor"]}\nevent: {kind}\ndata: {json.dumps(data)}\n\n'
                previous=signature
            elif ticks%40==0:yield ': heartbeat\n\n'
            ticks+=1
            await asyncio.sleep(.25)
    return StreamingResponse(events(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@app.get('/api/replay-sessions/{sid}/stories/{story_id}/evidence')
def evidence(sid:str,story_id:str,x_producer_token:str|None=Header(None)):
    with LOCK:
        s,at,p,status=authorized_package(sid,story_id,x_producer_token);meta,messages=inputs(s,at)
        start=p['metrics']['pressure_window_ms'][0];end=p['metrics']['retention_confirmed_at_ms']
        rows=EvidenceTools(meta,messages,at).get_sequence(start,end)
        frames=[{'time_ms':m['timeline_ms'],'payload':m['payload'],'message_id':m['message_id']} for m in rows if m['kind']=='tracking_frame']
        return {'story':p if producer(x_producer_token) else {k:p[k] for k in ['id','revision','title','claims','metrics','variants','evidence_revision']},'frames':frames,'events':[m for m in rows if m['kind']=='event'],'cutoff_ms':at,'status':status}

@app.get('/api/replay-sessions/{sid}/stories/{story_id}/variants')
def variants(sid:str,story_id:str,language:Literal['en','es']='en',detail:Literal['simple','detail']='simple',focus:str|None=None,x_producer_token:str|None=Header(None)):
    with LOCK:
        _,_,p,_=authorized_package(sid,story_id,x_producer_token)
        v=next((v for v in p['variants'] if v['language']==language and v['detail']==detail and v['focus']==focus),None)
        if not v:fail(400,'invalid_preference')
        return {**v,'story_id':story_id,'revision':p['revision']}

@app.post('/api/replay-sessions/{sid}/stories/{story_id}/review')
def review(sid:str,story_id:str,body:Review,x_producer_token:str|None=Header(None)):
    require(x_producer_token)
    with LOCK:
        request_hash=digest({'story_id':story_id,**body.model_dump()})
        old=repo.operation(sid,body.idempotency_key)
        if old:
            if old['request_hash']!=request_hash:fail(409,'idempotency_key_reused')
            return old['data']
        s,at,p,status=authorized_package(sid,story_id,x_producer_token)
        if body.expected_revision!=p['revision'] or body.package_hash!=p['package_hash']:fail(409,'stale_revision')
        if body.action in ('approve','edit') and at>=p['expires_at_ms']:fail(409,'expired')
        if body.action=='retract' and status not in ('approved','expired'):fail(409,'not_published')
        if body.action=='edit':
            if not body.text or not body.text.strip():fail(422,'edit_text_required')
            meta,messages=inputs(s,at);p=workflow(EvidenceTools(meta,messages,at),revision=p['revision']+1,proposed_text=body.text)
            if p is None:fail(422,'review_rejected')
            new_status='ready'
        else:new_status={'approve':'approved','suppress':'suppressed','retract':'retracted'}[body.action]
        result={'story_id':story_id,'status':new_status,'revision':p['revision'],'at_ms':at,'review':p['review']}
        # The repository commits decision, audit, and idempotency in one partition transaction.
        try:
            return repo.commit_review(sid,body.idempotency_key,request_hash,body.expected_revision,body.package_hash,p,new_status,at,result,edited=body.action=='edit')
        except RepositoryConflict as exc:fail(409,exc.code)

@app.post('/api/replay-sessions/{sid}/recaps')
def recap(sid:str,body:RecapRequest):
    with LOCK:
        s=get_session(sid); now=clock(s);cutoff=min(now,body.through_ms if body.through_ms is not None else now)
        p=materialize(s,now);decision=repo.decision(sid);moments=[]
        if p and decision and decision['status']=='approved' and decision['revision']==p['revision'] and decision['package_hash']==p['package_hash'] and decision['at_ms']<=cutoff and p['eligible_from_ms']<=cutoff:
            v=next(v for v in p['variants'] if v['language']==body.language and v['detail']=='simple' and v['focus'] is None)
            moments=[{'story_id':p['id'],'revision':p['revision'],'text':v['text'],'claim_ids':v['claim_ids']}]
        return {'title':'El partido hasta ahora' if body.language=='es' else 'Match so far','through_ms':cutoff,'moments':moments,'mode':'approved moments only'}

@app.get('/api/replay-sessions/{sid}/diagnostics')
def diagnostics(sid:str,x_producer_token:str|None=Header(None)):
    require(x_producer_token)
    with LOCK:
        s=get_session(sid);at=clock(s);p=materialize(s,at);meta,messages=inputs(s,at)
        usage=p.get('model_usage',{}) if p else {}
        return {'session_id':sid,'clock_ms':at,'mode':p['mode'] if p else runtime_mode(),'observations_delivered':len(available(messages,at)),'metric_version':'pressure-escape-v1','workflow_ms':p['workflow_ms'] if p else None,'trace':p['trace'] if p else [],'audit':repo.audit(sid),'azure_deployed':CLOUD,'model_calls':p.get('model_calls',usage.get('calls',0)) if p else 0,'model_tokens':p.get('model_tokens',usage.get('total_tokens',0)) if p else 0,'model_usage':usage,'transport':transport.diagnostics() if transport else {'mode':'local'},'workflow_pending':any(k[0]==sid and not f.done() for k,f in JOBS.items())}

_RATE=defaultdict(deque)
_RATE_LOCK=threading.Lock()
@app.middleware('http')
async def request_limits(request:Request,call_next):
    if CLOUD:
        try:body_size=int(request.headers.get('content-length','0'))
        except ValueError:return JSONResponse({'detail':{'code':'invalid_content_length'}},status_code=400)
        if body_size>65536:
            return JSONResponse({'detail':{'code':'request_too_large'}},status_code=413)
        key=(request.client.host if request.client else 'unknown',request.method=='POST')
        now=time.monotonic()
        with _RATE_LOCK:
            q=_RATE[key]
            while q and now-q[0]>60:q.popleft()
            if len(q)>=(60 if key[1] else 3000):
                return JSONResponse({'detail':{'code':'rate_limited'}},status_code=429,headers={'Retry-After':'60'})
            q.append(now)
    return await call_next(request)
