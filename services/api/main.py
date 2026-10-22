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
from engine.core import available, digest, load_match, metric, pass_metrics, visual_snapshot
from engine.catalog import list_matches, duration_for_match
from engine.repository import Repository
from engine.workflow import EvidenceTools, run_workflow
from engine.contextual_narrative import build_contextual_package as build_structured_package
from engine.context import contextual_metrics
from engine.recap import project_recap
from engine.editorial import decision_summary
from engine.dispositions import record, disposition, package_disposition
from engine.outcomes import create_outcome, start_outcome, finish_outcome

ROOT=Path(__file__).resolve().parents[2]
from engine.cloud_repository import CosmosRepository, RepositoryConflict
CLOUD=os.getenv('WHY_NOW_ENVIRONMENT')=='azure'
FOUNDRY=os.getenv('WHY_NOW_MODEL_MODE','template')=='foundry'
STRUCTURED=os.getenv('WHY_NOW_NARRATIVE_VERSION','3') in {'2','3'}
repo=CosmosRepository() if os.getenv('WHY_NOW_COSMOS_ENDPOINT') else Repository(os.getenv('WHY_NOW_DB',str(ROOT/'why_now.db')))
transport=None
if os.getenv('WHY_NOW_EVENTHUB_NAMESPACE'):
    from engine.transport import EventHubTransport
    transport=EventHubTransport(repo)
WORKERS=ThreadPoolExecutor(max_workers=2,thread_name_prefix='story')
JOBS={}
logger=logging.getLogger('whynow')
logger.setLevel(logging.INFO)

def workflow(tools,**kwargs):
    session_id=kwargs.pop('session_id','local')
    store=kwargs.pop('outcome_repository',repo)
    outcome=kwargs.pop('outcome',None)
    measured=tools.compute_pass_metrics()
    if STRUCTURED:
        measured=contextual_metrics(measured,tools.metadata,tools.messages,tools.cutoff_ms)
    if outcome is None:
        outcome=create_outcome(store,session_id,f'story-{tools.pass_id or (measured or {}).get("pass_id","unknown")}',
            (measured or {}).get('evidence_revision','unavailable'),kwargs.get('revision',1),tools.cutoff_ms,runtime_mode())
    outcome={**outcome,'evidence_observed_at':outcome['scheduled_at'],
             'implementation':{'schema_version':'3.0.0' if STRUCTURED else '1.0.0',
                               'prompt_version':'director-critic-v3.0' if STRUCTURED else 'legacy-v1',
                               'renderer_version':'context-claims-v3' if STRUCTURED else 'canonical-v1',
                               'metric_version':'pressure-escape-v1',
                               'tool_version':'evidence-tools-v3',
                               'context_version':'recent-completed-three-v1' if STRUCTURED else None,
                               'model_deployment':os.getenv('FOUNDRY_MODEL_DEPLOYMENT') if FOUNDRY else None,
                               'model_version':os.getenv('FOUNDRY_MODEL_VERSION') if FOUNDRY else None,
                               'release_commit':os.getenv('WHY_NOW_RELEASE_COMMIT','unknown')}}
    outcome=start_outcome(store,outcome)
    last={}
    def observe(event):
        nonlocal outcome,last
        last=event
        if event['state']=='started':
            outcome={**outcome,'model_usage':event['usage'],'trace':event['trace']}
            store.save_workflow_outcome(session_id,outcome)
    try:
        if FOUNDRY:
            from engine.foundry_workflow import run_foundry_workflow
            from engine.structured_workflow import run_structured_workflow
            from opentelemetry import trace
            with trace.get_tracer('whynow').start_as_current_span('story.workflow',attributes={'source.cutoff_ms':tools.cutoff_ms,'workflow.revision':kwargs.get('revision',1),'replay.session_id':session_id,'match.id':tools.metadata['match_id']}):
                runner=run_structured_workflow if STRUCTURED else run_foundry_workflow
                package=runner(tools,outcome_callback=observe,**kwargs)
        else:
            package=(build_structured_package if STRUCTURED else run_workflow)(tools,**kwargs)
        state=last.get('state') or ('produced' if package else 'abstained')
        zero={'calls':0,'input_tokens':0,'output_tokens':0,'total_tokens':0,'usage_complete':True}
        outcome=finish_outcome(store,outcome,state,package=package,usage=last.get('usage') or (zero if not FOUNDRY else None),
                       trace=last.get('trace'),reason=last.get('reason'))
        if package is None:
            disposition(store,session_id,outcome,'not_produced',at_ms=tools.cutoff_ms)
        return package
    except Exception:
        if outcome['state'] in {'scheduled','started'}:
            finish_outcome(store,outcome,'failed',usage=last.get('usage'),trace=last.get('trace'),reason='workflow_or_persistence_failure')
        raise

def inputs(session,at):
    meta,messages=load_match(session['match_id'])
    return meta,transport.messages(session,at) if transport else messages

def runtime_mode():return 'Microsoft Agent Framework + Azure OpenAI' if FOUNDRY else 'local deterministic template'

@asynccontextmanager
async def lifespan(app):
    if CLOUD and (not os.getenv('WHY_NOW_PRODUCER_TOKEN') or TOKEN=='local-demo-producer' or len(TOKEN)<24):
        raise RuntimeError('Cloud deployment requires a private producer key of at least 24 characters')
    repo.interrupt_workflow_outcomes()
    if transport:transport.start()
    yield
    if transport:transport.close()

TOKEN=os.getenv('WHY_NOW_PRODUCER_TOKEN','local-demo-producer')
LOCK=threading.RLock()
app=FastAPI(title='WHY/NOW',version='0.4.0',lifespan=lifespan)
if os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING'):
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    configure_azure_monitor(logger_name='whynow',enable_live_metrics=False,sampling_ratio=0.1)
    FastAPIInstrumentor.instrument_app(app)

app.add_middleware(CORSMiddleware,allow_origins=os.getenv('WHY_NOW_ORIGINS','http://localhost:3000,http://127.0.0.1:3000').split(','),allow_methods=['GET','POST'],allow_headers=['Content-Type','X-Producer-Token','Last-Event-ID'])

class Body(BaseModel): model_config=ConfigDict(extra='forbid')
class Create(Body): match_id:str=Field(default='match-001',min_length=1,max_length=80)
class Control(Body):
    action:Literal['start','pause','speed','reset','seek']
    speed:float|None=Field(default=None,ge=.25,le=8,allow_inf_nan=False)
    clock_ms:int|None=Field(default=None,ge=0,le=5400000)
class Review(Body):
    action:Literal['approve','suppress','retract','edit']
    expected_revision:int=Field(ge=1)
    package_hash:str=Field(min_length=64,max_length=64)
    idempotency_key:str=Field(min_length=8,max_length=100)
    text:str|None=Field(default=None,max_length=1000)
    angle:Literal['progression','reception','historical_contrast']|None=None
class RecapRequest(Body):
    through_ms:int|None=Field(default=None,ge=0,le=5400000)
    language:Literal['en','es']='en'
    focus:str|None=Field(default=None,max_length=80)


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
    return min(s.get('duration_ms',60000),int(s['clock_ms']+elapsed))

def new_session(match_id):
    s={'id':str(uuid.uuid4()),'match_id':match_id,'clock_ms':0,'running':False,'speed':1,'updated_at':time.time(),'generation':1,'control_revision':1,'duration_ms':duration_for_match(match_id)}
    repo.save_session(s);return s

def accept_package(sid,package,at,expected_revision):
    try:
        repo.store_package(sid,package,at,expected_revision=expected_revision)
    except RepositoryConflict:
        raise
    except Exception:
        package_disposition(repo,sid,package,'persistence_failed',at)
        raise
    package_disposition(repo,sid,package,'accepted',at)

def materialize_all(s,at):
    """Each pass owns its evidence, workflow, revision and publication decision."""
    meta,messages=inputs(s,at)
    stored={p['id']:p for p in repo.list_packages(s['id'])}
    raw_measured={f"story-{m['pass_id']}":m for m in pass_metrics(messages,at,meta)}
    measured={key:contextual_metrics(m,meta,messages,at) if STRUCTURED else m
              for key,m in raw_measured.items()}
    # Stored approved v1/v2 packages keep their original revision and rendering.
    # A changed current source still invalidates them through the existing path.
    for key,old in stored.items():
        if old['schema_version']!='3.0.0' and key in raw_measured:
            if old['evidence_revision']==raw_measured[key]['evidence_revision']:
                measured[key]=raw_measured[key]
    for story_id,old in stored.items():
        m=measured.get(story_id)
        if not m or not m['eligible'] or old['evidence_revision']!=m['evidence_revision']:
            decision=repo.decision(s['id'],story_id)
            if decision and decision['status']!='superseded':
                repo.invalidate(s['id'],story_id)
                package_disposition(repo,s['id'],old,'superseded',at)
    packages=[]
    for story_id,m in measured.items():
        if not m['eligible']:continue
        opportunity_id=[story_id,m['evidence_revision']]
        record(repo,s['id'],'opportunity',[*opportunity_id,'detected'],story_id=story_id,
               evidence_revision=m['evidence_revision'],state='detected',replay_ms=at)

        old=stored.get(story_id)
        if old and old['evidence_revision']==m['evidence_revision']:
            packages.append(old)
            continue
        revision=old['revision']+1 if old else 1
        tools=EvidenceTools(meta,messages,at,pass_id=m['pass_id'])
        if not FOUNDRY:
            package=workflow(tools,revision=revision,session_id=s['id'])
            if package:
                accept_package(s['id'],package,at,expected_revision=revision-1)
                packages.append(package)
            continue
        key=(s['id'],story_id,m['evidence_revision'])
        future=JOBS.get(key)
        if future is None:
            # Never spend model calls on a new, already-expired live candidate.
            if at>=m['retention_confirmed_at_ms']+30000:
                record(repo,s['id'],'opportunity',[*opportunity_id,'expired_unscheduled'],story_id=story_id,
                       evidence_revision=m['evidence_revision'],state='expired_unscheduled',replay_ms=at)
                continue
            if sum(not f.done() for f in JOBS.values())>=4:
                record(repo,s['id'],'opportunity',[*opportunity_id,'capacity_deferred'],story_id=story_id,
                       evidence_revision=m['evidence_revision'],state='capacity_deferred',replay_ms=at)
                continue
            outcome=create_outcome(repo,s['id'],story_id,m['evidence_revision'],revision,at,runtime_mode())
            future=WORKERS.submit(workflow,tools,revision=revision,session_id=s['id'],outcome=outcome,outcome_repository=repo)
            future._why_now_run_id=outcome['run_id']
            JOBS[key]=future
            continue
        if not future.done():continue
        try:
            package=future.result()
            if package:
                if at>=m['retention_confirmed_at_ms']+30000:
                    package_disposition(repo,s['id'],package,'expired_before_acceptance',at)
                    continue
                # Results were generated against frozen scoped evidence; only
                # this current-evidence key may commit. A stale job is ignored.
                if package['id']!=story_id or package['evidence_revision']!=m['evidence_revision']:
                    raise ValueError('workflow_scope_mismatch')
                accept_package(s['id'],package,at,expected_revision=revision-1)
                packages.append(package)
                logger.info('workflow_complete session=%s story=%s revision=%s mode=%s usage=%s',s['id'],story_id,revision,package['mode'],package.get('model_usage',{}))
        except RepositoryConflict:
            latest=repo.latest_package(s['id'],story_id)
            if latest and latest['evidence_revision']==m['evidence_revision']:packages.append(latest)
        except Exception:
            # Suppress repeated exception logging for the same completed job.
            if not getattr(future,'_why_now_logged',False):
                logger.exception('workflow_failed session=%s story=%s',s['id'],story_id)
                future._why_now_logged=True
    for key,future in JOBS.items():
        if key[0]!=s['id'] or not future.done():continue
        current=measured.get(key[1])
        if current and current['eligible'] and current['evidence_revision']==key[2]:continue
        run_id=getattr(future,'_why_now_run_id',None)
        outcome=next((o for o in repo.workflow_outcomes(s['id']) if o['run_id']==run_id),None)
        if outcome:
            disposition(repo,s['id'],outcome,'discarded_stale',at_ms=at)
    # Bound retained completed jobs; running work always keeps its slot/identity.
    for key in list(JOBS):
        if len(JOBS)<=512:break
        if JOBS[key].done():del JOBS[key]
    return sorted(packages,key=lambda p:(p['eligible_from_ms'],p['id']))


def materialize(s,at,story_id=None):
    packages=materialize_all(s,at)
    if story_id is not None:return next((p for p in packages if p['id']==story_id),None)
    return packages[-1] if packages else None


def publication(s,package,at):
    if not package:return 'none',None
    decision=repo.decision(s['id'],package['id'])
    status=decision['status'] if decision and decision['revision']==package['revision'] and decision['package_hash']==package['package_hash'] else 'ready'
    if at>=package['expires_at_ms'] and status in ('approved','ready'):status='expired'
    published=bool(decision and decision['status']=='approved' and decision['revision']==package['revision'] and decision['package_hash']==package['package_hash'] and decision['at_ms']<=at and package['eligible_from_ms']<=at)
    return status,package if published else None

def safe_story(package,status):
    if not package:return None
    titles={}
    if package['schema_version']=='3.0.0':
        from engine.contextual_narrative import title_for
        titles={lang:title_for(package['narrative_plan'],package['metrics'],lang) for lang in ['en','es']}
    return {k:package[k] for k in ['id','revision','title','evidence_revision','eligible_from_ms','expires_at_ms']}|{'titles':titles}|{'status':status}|{k:package['metrics'][k] for k in ['passer_id','receiver_id','team_id']}

def snapshot_data(sid,is_producer=False,story_id=None):
    with LOCK:
        s=get_session(sid);at=clock(s);meta,messages=inputs(s,at)
        packages=materialize_all(s,at)
        entries=[(p,*publication(s,p,at)) for p in packages]
        visible=[(p,status,published) for p,status,published in entries if is_producer or published]
        selected=next((entry for entry in visible if entry[0]['id']==story_id),None) if story_id else None
        if selected is None and visible:selected=visible[-1]
        current,status,_=selected if selected else (None,'waiting',None)
        live=[p for p,state,published in entries if published and state=='approved']
        overlay_package=live[-1] if live else None
        def summary(p,state,published):
            result=safe_story(p,state)
            result['approved']=published is not None
            if is_producer:result['package_hash']=p['package_hash']
            return result
        view=visual_snapshot(messages,at)
        audit=repo.audit(sid)
        duration=s.get('duration_ms',60000)
        return {'session_id':sid,'match_id':s['match_id'],'clock_ms':at,'duration_ms':duration,
                'running':s['running'] and at<duration,'speed':s['speed'],'synthetic':True,
                'score':meta['initial_state']['score'],'teams':meta['teams'],'players':meta['players'],**view,
                'story':summary(current,status,selected[2]) if current else None,
                'stories':[summary(p,state,published) for p,state,published in visible],
                'story_status':status,'overlay_story_id':overlay_package['id'] if overlay_package else None,
                'overlay':next(v['text'] for v in overlay_package['variants'] if v['id']=='en_simple_general') if overlay_package else None,
                'mode':current['mode'] if current else runtime_mode(),
                'workflow_pending':any(k[0]==sid and not f.done() for k,f in JOBS.items()),
                'cursor':len(audit)*10000000+s['control_revision']*10000000+at,
                'generation':s['generation']}


def authorized_package(sid,story_id,token=None):
    s=get_session(sid);at=clock(s);p=materialize(s,at,story_id)
    if not p:fail(404,'story_unavailable')
    status,published=publication(s,p,at)
    if not producer(token) and not published:fail(404,'story_unavailable')
    return s,at,p,status

@app.get('/api/health')
def health():return {'ok':True,'mode':runtime_mode(),'azure_deployed':CLOUD,'version':'0.4.0','narrative_version':'2' if STRUCTURED else '1'}

@app.get('/api/ready')
def ready():
    if CLOUD:
        repo.list_sessions()
        if transport and transport.diagnostics().get('last_error'):fail(503,'transport_not_ready')
    return {'ok':True,'persistence':'cosmos' if isinstance(repo,CosmosRepository) else 'sqlite','transport':'eventhubs' if transport else 'local','model':runtime_mode()}


@app.get('/api/matches')
def matches():return {'matches':list_matches()}


@app.post('/api/replay-sessions')
def create(body:Create,x_producer_token:str|None=Header(None)):
    require(x_producer_token)
    if body.match_id not in {m['match_id'] for m in list_matches()}:fail(422,'unknown_match')
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
        if body.action=='seek':
            if body.clock_ms is None:fail(422,'seek_clock_required')
            if body.clock_ms<at:fail(409,'seek_forward_only')
            s['clock_ms']=min(body.clock_ms,s.get('duration_ms',60000));s['running']=False
        if body.action=='start':s['running']=True
        elif body.action=='pause':s['running']=False
        if body.speed is not None:s['speed']=body.speed
        repo.save_session(s)
        return {'session_id':sid,'clock_ms':s['clock_ms'],'running':s['running'],'speed':s['speed']}

@app.get('/api/replay-sessions/{sid}/snapshot')
def snapshot(sid:str,x_producer_token:str|None=Header(None),story_id:str|None=None):
    return snapshot_data(sid,producer(x_producer_token),story_id)

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
        if body.action=='retract':
            decision=repo.decision(sid,story_id)
            if not decision or decision['status']!='approved' or decision['revision']!=p['revision'] or decision['package_hash']!=p['package_hash']:
                fail(409,'not_published')
        if body.action=='edit':
            if not body.angle and (not body.text or not body.text.strip()):fail(422,'edit_text_required')
            if body.angle and not STRUCTURED:fail(422,'emphasis_requires_structured_package')
            if body.angle=='historical_contrast' and 'c-context' not in {c['id'] for c in p['claims']}:
                fail(422,'historical_contrast_requires_evidence')
            meta,messages=inputs(s,at);p=workflow(EvidenceTools(meta,messages,at,pass_id=p['metrics']['pass_id']),revision=p['revision']+1,proposed_text=body.text,session_id=sid,**({'editorial_angle':body.angle} if body.angle else {}))
            if p is None:fail(422,'review_rejected')
            new_status='ready'
        else:new_status={'approve':'approved','suppress':'suppressed','retract':'retracted'}[body.action]
        record(repo,sid,'approval_received',[body.idempotency_key,body.action],story_id=story_id,revision=p['revision'],action=body.action,replay_ms=at)
        result={'story_id':story_id,'status':new_status,'revision':p['revision'],'at_ms':at,'review':p['review']}
        # The repository commits decision, audit, and idempotency in one partition transaction.
        try:
            return repo.commit_review(sid,body.idempotency_key,request_hash,body.expected_revision,body.package_hash,p,new_status,at,result,edited=body.action=='edit')
        except RepositoryConflict as exc:fail(409,exc.code)

class BrowserAck(Body):
    revision:int=Field(ge=1)
    evidence_revision:str=Field(min_length=16,max_length=64)
    event_id:uuid.UUID
    paint_interval_ms:float=Field(ge=0,le=60000,allow_inf_nan=False)

@app.post('/api/replay-sessions/{sid}/stories/{story_id}/render-ack')
def render_ack(sid:str,story_id:str,body:BrowserAck):
    with LOCK:
        _,at,p,_=authorized_package(sid,story_id,None)
        if p['revision']!=body.revision or p['evidence_revision']!=body.evidence_revision:
            fail(409,'stale_render_identity')
        event=record(repo,sid,'browser_ack',[story_id,body.revision],story_id=story_id,
                     revision=body.revision,evidence_revision=body.evidence_revision,
                     event_id=str(body.event_id),paint_interval_ms=body.paint_interval_ms,replay_ms=at,
                     clock_scope='Browser monotonic interval only; no server/browser clock subtraction.')
        return {'recorded_at':event['recorded_at'],'event_id':event['event_id']}

@app.post('/api/replay-sessions/{sid}/recaps')
def recap(sid:str,body:RecapRequest):
    with LOCK:
        s=get_session(sid);now=clock(s);cutoff=min(now,body.through_ms if body.through_ms is not None else now)
        approved=[]
        for p in materialize_all(s,now):
            decision=repo.decision(sid,p['id'])
            if decision and decision['status']=='approved' and decision['revision']==p['revision'] and decision['package_hash']==p['package_hash'] and decision['at_ms']<=cutoff and p['eligible_from_ms']<=cutoff:
                approved.append(p)
        if body.focus and body.focus not in {x['id'] for x in inputs(s,now)[0]['players']+inputs(s,now)[0]['teams']}:
            fail(400,'invalid_preference')
        return {'title':'El partido hasta ahora' if body.language=='es' else 'Match so far',
                'through_ms':cutoff, 'mode':'approved moments only',
                **project_recap(approved,body.language,cutoff,body.focus)}

@app.get('/api/replay-sessions/{sid}/diagnostics')
def diagnostics(sid:str,x_producer_token:str|None=Header(None),story_id:str|None=None):
    require(x_producer_token)
    with LOCK:
        s=get_session(sid);at=clock(s);p=materialize(s,at,story_id);meta,messages=inputs(s,at)
        usage=p.get('model_usage',{}) if p else {}
        outcomes=repo.workflow_outcomes(sid)
        if story_id:outcomes=[o for o in outcomes if o['story_id']==story_id]
        return {'session_id':sid,'clock_ms':at,'mode':p['mode'] if p else runtime_mode(),'observations_delivered':len(available(messages,at)),'ingestion_lag_ms':max(0,at-max((m['available_at_ms'] for m in available(messages,at)),default=0)),'metric_version':'pressure-escape-v1','workflow_ms':p['workflow_ms'] if p else None,'trace':p['trace'] if p else [],'audit':repo.audit(sid),'azure_deployed':CLOUD,'model_calls':p.get('model_calls',usage.get('calls',0)) if p else 0,'model_tokens':p.get('model_tokens',usage.get('total_tokens',0)) if p else 0,'model_usage':usage,'workflow_outcomes':outcomes,'lifecycle_events':repo.lifecycle_events(sid),'decision_summary':decision_summary(p,outcomes),'transport':transport.diagnostics() if transport else {'mode':'local'},'workflow_pending':any(k[0]==sid and not f.done() for k,f in JOBS.items())}

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
