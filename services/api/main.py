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
from engine.catalog import list_matches, duration_for_match, development_matches
from engine.repository import Repository
from engine.workflow import EvidenceTools, run_workflow
from engine.editorial_narrative import build_editorial_package as build_structured_package
from engine.context import contextual_metrics
from engine.recap import project_recap
from engine.public_updates import record_source_withdrawal, public_updates
from engine.editorial import decision_summary
from engine.event_metrics import event_metrics, FAMILY_PRIORITY
from engine.event_narrative import build_event_package, story_id as event_story_id, display_title
from engine.match_state import match_state
from engine.event_workflow import generate_event
COVERAGE=os.getenv('WHY_NOW_MATCH_COVERAGE','0')=='1'
DEVELOPMENT=COVERAGE and os.getenv('WHY_NOW_SYNTHETIC_DEVELOPMENT','0')=='1'
DEVELOPMENT_IDS={r['match_id'] for r in development_matches()}
FLAGSHIP_IDS={'match-0c0a000000000005','match-0c0a000000000006','match-0c0a000000000007','match-0c0a000000000008'}
PRESENTATION_IDS={'match-0c0a000000000003','match-0c0a000000000004'}|FLAGSHIP_IDS
MIXED_IDS={'match-0c0a000000000001','match-0c0a000000000002'}|PRESENTATION_IDS
MIXED_IDS |= DEVELOPMENT_IDS
PRESSURE_IDS=FLAGSHIP_IDS|DEVELOPMENT_IDS
from engine.dispositions import record, disposition, package_disposition, package_events, reconcile_acceptances
from engine.outcomes import create_outcome, start_outcome, finish_outcome

ROOT=Path(__file__).resolve().parents[2]
from engine.cloud_repository import CosmosRepository, RepositoryConflict
CLOUD=os.getenv('WHY_NOW_ENVIRONMENT')=='azure'
FOUNDRY=os.getenv('WHY_NOW_MODEL_MODE','template')=='foundry'
EVENT_MODEL=os.getenv('WHY_NOW_MATCH_MODEL','0')=='1' and FOUNDRY
STRUCTURED=os.getenv('WHY_NOW_NARRATIVE_VERSION','3') in {'2','3'}
repo=CosmosRepository() if os.getenv('WHY_NOW_COSMOS_ENDPOINT') else Repository(os.getenv('WHY_NOW_DB',str(ROOT/'why_now.db')))
transport=None
if os.getenv('WHY_NOW_EVENTHUB_NAMESPACE'):
    from engine.transport import EventHubTransport
    transport=EventHubTransport(repo)
WORKERS=ThreadPoolExecutor(max_workers=2,thread_name_prefix='story')
JOBS={}
LIVE_MEASURED={}
logger=logging.getLogger('matchsense')
logger.setLevel(logging.INFO)

class OAuthAccessLogFilter(logging.Filter):
    """Keep OAuth callback codes and state out of local/server access logs."""
    def filter(self, record):
        args=record.args
        if record.name=='uvicorn.access' and isinstance(args,tuple) and len(args)>=3:
            request_target=str(args[2])
            if '/api/youtube/oauth/callback' in request_target and '?' in request_target:
                safe=list(args);safe[2]=request_target.split('?',1)[0]+'?[redacted]';record.args=tuple(safe)
        return True

logging.getLogger('uvicorn.access').addFilter(OAuthAccessLogFilter())

def workflow(tools,**kwargs):
    force_template=kwargs.pop('force_template',False)
    use_model=FOUNDRY and not force_template
    session_id=kwargs.pop('session_id','local')
    store=kwargs.pop('outcome_repository',repo)
    outcome=kwargs.pop('outcome',None)
    measured=tools.compute_pass_metrics()
    if STRUCTURED:
        measured=contextual_metrics(measured,tools.metadata,tools.messages,tools.cutoff_ms)
    if outcome is None:
        outcome=create_outcome(store,session_id,f'story-{tools.pass_id or (measured or {}).get("pass_id","unknown")}',
            (measured or {}).get('evidence_revision','unavailable'),kwargs.get('revision',1),tools.cutoff_ms,runtime_mode() if use_model else 'local deterministic template')
    outcome={**outcome,'evidence_observed_at':outcome['scheduled_at'],
             'implementation':{'schema_version':'4.0.0' if STRUCTURED else '1.0.0',
                               'prompt_version':'director-critic-v4.1' if STRUCTURED else 'legacy-v1',
                               'renderer_version':'editorial-claims-v4' if STRUCTURED else 'canonical-v1',
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
        if use_model:
            from engine.foundry_workflow import run_foundry_workflow
            from engine.structured_workflow import run_structured_workflow
            from opentelemetry import trace
            with trace.get_tracer('matchsense').start_as_current_span('story.workflow',attributes={'source.cutoff_ms':tools.cutoff_ms,'workflow.revision':kwargs.get('revision',1),'replay.session_id':session_id,'match.id':tools.metadata['match_id']}):
                runner=run_structured_workflow if STRUCTURED else run_foundry_workflow
                package=runner(tools,outcome_callback=observe,**kwargs)
        else:
            package=(build_structured_package if STRUCTURED else run_workflow)(tools,**kwargs)
        state=last.get('state') or ('produced' if package else 'abstained')
        zero={'calls':0,'input_tokens':0,'output_tokens':0,'total_tokens':0,'usage_complete':True}
        outcome=finish_outcome(store,outcome,state,package=package,usage=last.get('usage') or (zero if not use_model else None),
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
    reconcile_acceptances(repo)
    if transport:transport.start()
    stop=threading.Event()
    worker=threading.Thread(target=live_worker,args=(stop,),daemon=True,name='live-match-processor')
    worker.start()
    try:yield
    finally:
        stop.set();worker.join(timeout=10)
        if transport:transport.close()

TOKEN=os.getenv('WHY_NOW_PRODUCER_TOKEN','local-demo-producer')
LOCK=threading.RLock()
app=FastAPI(title='MatchSense',version='0.5.0',lifespan=lifespan)
if os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING'):
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    configure_azure_monitor(logger_name='matchsense',enable_live_metrics=False,sampling_ratio=0.1)
    # OAuth authorization codes and state arrive as callback query parameters.
    # Keep that one route out of request telemetry while preserving workflow traces.
    FastAPIInstrumentor.instrument_app(app, excluded_urls=r"/api/youtube/oauth/callback")

app.add_middleware(CORSMiddleware,allow_origins=os.getenv('WHY_NOW_ORIGINS','http://localhost:3000,http://127.0.0.1:3000').split(','),allow_methods=['GET','POST'],allow_headers=['Content-Type','X-Producer-Token','Last-Event-ID'])

class Body(BaseModel): model_config=ConfigDict(extra='forbid')
class Create(Body):
    match_id:str=Field(default='match-001',min_length=1,max_length=80)
    mode:Literal['guided','live']='guided'
    execution:Literal['configured','ai','template']='configured'
class Control(Body):
    action:Literal['start','pause','speed','reset','seek','stop']
    speed:float|None=Field(default=None,ge=.25,le=8,allow_inf_nan=False)
    clock_ms:int|None=Field(default=None,ge=0,le=5400000)
class Review(Body):
    action:Literal['approve','approve_archive','suppress','retract','edit']
    expected_revision:int=Field(ge=1)
    package_hash:str=Field(min_length=64,max_length=64)
    idempotency_key:str=Field(min_length=8,max_length=100)
    text:str|None=Field(default=None,max_length=1000)
    angle:Literal['progression','reception','historical_contrast']|None=None
class RecapRequest(Body):
    from_ms:int|None=Field(default=None,ge=0,le=5400000)
    through_ms:int|None=Field(default=None,ge=0,le=5400000)
    language:Literal['en','es']='en'
    focus:str|None=Field(default=None,max_length=80)


def fail(status,code): raise HTTPException(status,detail={'code':code})
def require(token):
    if not token or not secrets.compare_digest(token,TOKEN):fail(401,'producer_auth_required')

from services.api.obs_status import create_obs_router
app.include_router(create_obs_router(require))

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

def new_session(match_id,mode="guided",execution="configured"):
    execution_explicit=execution!="configured"
    execution=("ai" if FOUNDRY else "template") if execution=="configured" else execution
    s={'id':str(uuid.uuid4()),'match_id':match_id,'match_coverage':COVERAGE and match_id in MIXED_IDS,'clock_ms':0,'running':False,'speed':1,'updated_at':time.time(),'generation':1,'control_revision':1,'duration_ms':duration_for_match(match_id)}
    s.update(session_mode=mode,execution=execution,execution_explicit=execution_explicit,running=mode=='live',model_identity={'deployment':os.getenv('FOUNDRY_MODEL_DEPLOYMENT'),'version':os.getenv('FOUNDRY_MODEL_VERSION')} if execution=='ai' else None)
    repo.save_session(s);return s

def accept_package(sid,package,at,expected_revision):
    events=package_events(repo,sid,package,'accepted',at)
    try:
        repo.store_package(sid,package,at,expected_revision=expected_revision,acceptance_events=events)
    except Exception as exc:
        # A committed transaction can lose its response. Exact retries repair the
        # ledger without advancing a pointer, changing approval, or spending AI.
        latest=repo.latest_package(sid,package['id'])
        if latest and all(latest[k]==package[k] for k in ('id','revision','package_hash')):
            reconcile_acceptances(repo,sid)
            return
        if not isinstance(exc,RepositoryConflict):
            package_disposition(repo,sid,package,'persistence_failed',at)
        raise


def model_workflow_configured():
    """Whether replay workflows can call the configured Agent Framework model."""
    return bool(FOUNDRY and os.getenv('AZURE_OPENAI_ENDPOINT') and os.getenv('FOUNDRY_MODEL_DEPLOYMENT'))


def live_ai_configured():
    """Whether continuous live mode also has its event-model integration enabled."""
    return bool(EVENT_MODEL and model_workflow_configured())


def live_attempt_blocked(s,story_id,evidence_revision,at):
    if s.get('session_mode')!='live':return False
    outcomes=repo.workflow_outcomes(s['id'])
    same=[o for o in outcomes if o['story_id']==story_id and o['evidence_revision']==evidence_revision]
    # After a restart, preserve rejected/failed attempts. Retry interrupted or
    # produced-but-not-persisted work once, retaining both usage records.
    blocked=bool(same and (len(same)>=2 or same[-1]['state'] not in {'interrupted','produced'}))
    reserved=sum(6 if o['story_id'].startswith('story-pass-') else 2 for o in outcomes)
    needed=6 if story_id.startswith('story-pass-') else 2
    if blocked or reserved+needed>96:
        record(repo,s['id'],'opportunity',[story_id,evidence_revision,'attempt_limit'],story_id=story_id,state='attempt_or_session_budget_limit',replay_ms=at)
        return True
    return False


def live_attempt_summary(sid,at):
    return [{'story_id':o['story_id'],'state':o['state'],'reason':o.get('reason'),
             'mode':o['mode'],'usage':o['model_usage'],'scheduled_at':o['scheduled_at'],
             'finished_at':o.get('finished_at'),'cutoff_ms':o['cutoff_ms']}
            for o in repo.workflow_outcomes(sid)]


def live_tick():
    """Progress live sessions without page reads. Single execution host only."""
    with LOCK:sessions=repo.list_sessions()
    for previous in sessions:
        with LOCK:
            s=get_session(previous['id'])
            if s.get('session_mode')!='live':continue
            if s.get('ended_early'):
                if s.get('ended_cleanup_done'):continue
                pending=False
                for key,future in JOBS.items():
                    if key[0]!=s['id']:continue
                    if not future.done():
                        pending=True;continue
                    outcome=next((o for o in repo.workflow_outcomes(s['id']) if o['run_id']==getattr(future,'_why_now_run_id',None)),None)
                    if outcome:disposition(repo,s['id'],outcome,'session_ended',at_ms=clock(s))
                if not pending:
                    s['ended_cleanup_done']=True;repo.save_session(s)
                continue
            if not s['running']:continue
            at=clock(s)
            try:
                packages=materialize_all(s,at)
                s['available_story_ids']=[p['id'] for p in packages]
                s['last_processed_ms']=at
                pending=any(k[0]==s['id'] and not f.done() for k,f in JOBS.items())
                if at>=s['duration_ms'] and not pending:
                    s.update(clock_ms=s['duration_ms'],running=False,updated_at=time.time())
                repo.save_session(s)
            except Exception:
                logger.exception('live_tick_failed session=%s',s['id'])


def live_worker(stop):
    while not stop.is_set():
        try:live_tick()
        except Exception:logger.exception('live_worker_failed')
        stop.wait(1)


def materialize_all(s,at):
    """Dispatch supported families through shared immutable approval accounting."""
    meta,messages=inputs(s,at)
    use_model=(FOUNDRY if s.get('session_mode')!='live' and not s.get('execution_explicit') else s.get('execution','ai' if FOUNDRY else 'template')=='ai')
    if s.get('ended_early'):return repo.list_packages(s['id'])
    model_available=not use_model or (FOUNDRY and (s.get('session_mode')!='live' or live_ai_configured()))
    stored={p['id']:p for p in repo.list_packages(s['id'])}
    cache_key=None
    cached=None
    if s.get('session_mode')=='live' and transport is None:
        # Ordinary frame arrivals may delay a candidate by at most one source
        # second. Every explicit event, delayed sample and correction bypasses
        # that cache immediately; no future source enters a measurement.
        delivered_changes=sum(1 for r in messages if r['available_at_ms']<=at and r['timeline_ms']<=at and (r['kind']=='event' or r['revision']>1 or r['available_at_ms']>r['timeline_ms']))
        cache_key=(id(messages),at//1000,delivered_changes)
        cached=LIVE_MEASURED.get(s['id'])
    if cached and cached[0]==cache_key:
        raw_measured,measured=cached[1],dict(cached[2])
    else:
        raw_measured={f"story-{m['pass_id']}":m for m in pass_metrics(messages,at,meta)}
        measured={key:contextual_metrics(m,meta,messages,at) if STRUCTURED else m
                  for key,m in raw_measured.items()}
        coverage=s.get('match_coverage',COVERAGE and s['match_id'] in MIXED_IDS)
        if coverage:
            measured.update({event_story_id(m):m for m in event_metrics(meta,messages,at)})
            if s['match_id'] in PRESSURE_IDS:
                from engine.pressure import pressure_metrics
                measured.update({event_story_id(m):m for m in pressure_metrics(meta,messages,at)})
        if cache_key:
            LIVE_MEASURED[s['id']]=(cache_key,raw_measured,dict(measured))
            while len(LIVE_MEASURED)>128:LIVE_MEASURED.pop(next(iter(LIVE_MEASURED)))
    coverage=s.get('match_coverage',COVERAGE and s['match_id'] in MIXED_IDS)
    # Stored approved v1/v2 packages keep their original revision and rendering.
    # A changed current source still invalidates them through the existing path.
    for key,old in stored.items():
        if old['schema_version'] not in {'3.0.0','4.0.0'} and key in raw_measured:
            if old['evidence_revision']==raw_measured[key]['evidence_revision']:
                measured[key]=raw_measured[key]
    for story_id,old in stored.items():
        m=measured.get(story_id)
        if not m or not m['eligible'] or old['evidence_revision']!=m['evidence_revision']:
            decision=repo.decision(s['id'],story_id)
            if decision and decision['status']!='superseded':
                if decision['status']=='approved' and decision['revision']==old['revision'] and decision['package_hash']==old['package_hash']:
                    record_source_withdrawal(repo,s['id'],old,at)
                repo.invalidate(s['id'],story_id)
                package_disposition(repo,s['id'],old,'superseded',at)
    packages=[]
    ordered=sorted(measured.items(),key=lambda item:(FAMILY_PRIORITY.get(item[1].get('family','pass'),4),-item[1].get('occurrence_ms',item[1].get('available_from_ms',0)),item[0])) if coverage else measured.items()
    for story_id,m in ordered:
        if not m['eligible']:continue
        if s.get('session_mode')=='live' and m.get('family')=='possession' and int(m['subject_id'])%60000:
            record(repo,s['id'],'opportunity',[story_id,'editorial_interval'],story_id=story_id,state='not_selected_live_possession_interval',replay_ms=at)
            continue
        if s.get('session_mode')=='live':
            # Stabilize the already-defined follow-up evidence before spending
            # model calls on successive revisions of the same incident.
            waiting=(m.get('family')=='recovery' and at<m['occurrence_ms']+3000)
            waiting=waiting or (m.get('family')=='shot' and m['facts'].get('reported_outcome')=='goal' and m['facts'].get('goal_status') not in {'confirmed','cancelled'} and at<m['occurrence_ms']+6000)
            if waiting:
                record(repo,s['id'],'opportunity',[story_id,'awaiting_followup'],story_id=story_id,state='awaiting_source_followup',replay_ms=at)
                continue
        opportunity_id=[story_id,m['evidence_revision']]
        old=stored.get(story_id)
        if old and old['evidence_revision']==m['evidence_revision']:
            packages.append(old)
            continue
        if not model_available:
            record(repo,s['id'],'opportunity',[*opportunity_id,'ai_unavailable'],story_id=story_id,state='ai_unavailable',replay_ms=at)
            continue
        record(repo,s['id'],'opportunity',[*opportunity_id,'detected'],story_id=story_id,
               evidence_revision=m['evidence_revision'],state='detected',replay_ms=at)
        revision=old['revision']+1 if old else 1
        if m.get('family'):
            if m['family']=='possession':
                for previous in stored.values():
                    if previous.get('family')!='possession' or previous['eligible_from_ms']>=m['evidence_ready_ms']:continue
                    decision=repo.decision(s['id'],previous['id'])
                    if not decision or decision['status']!='approved':package_disposition(repo,s['id'],previous,'replaced_unreviewed',at)
            if EVENT_MODEL and (use_model or (s.get('session_mode')!='live' and not s.get('execution_explicit'))):
                key=(s['id'],story_id,m['evidence_revision'])
                future=JOBS.get(key)
                if future is None:
                    if live_attempt_blocked(s,story_id,m['evidence_revision'],at):continue
                    state='expired_unscheduled' if at>=m['expires_at_ms'] or (s.get('session_mode')=='live' and at>=s['duration_ms']) else 'capacity_deferred' if sum(not f.done() for f in JOBS.values())>=4 else None
                    if state:
                        record(repo,s['id'],'opportunity',[*opportunity_id,state],story_id=story_id,family=m['family'],state=state,replay_ms=at)
                        continue
                    outcome=create_outcome(repo,s['id'],story_id,m['evidence_revision'],revision,at,'Microsoft Agent Framework + Azure OpenAI')
                    future=WORKERS.submit(generate_event,repo,s['id'],m,meta,messages,at,revision,True,outcome)
                    future._why_now_run_id=outcome['run_id']
                    JOBS[key]=future
                    continue
                if not future.done():continue
                try:package=future.result()
                except Exception:
                    record(repo,s['id'],'opportunity',[*opportunity_id,'failed'],story_id=story_id,state='workflow_failed',replay_ms=at)
                    continue
                if not package:continue
                if at>=m['expires_at_ms']:
                    package_disposition(repo,s['id'],package,'expired_before_acceptance',at)
                    continue
                if package['evidence_revision']!=m['evidence_revision'] or package['id']!=story_id:
                    package_disposition(repo,s['id'],package,'discarded_stale',at)
                    continue
            else:
                package=generate_event(repo,s['id'],m,meta,messages,at,revision)
            accept_package(s['id'],package,at,expected_revision=revision-1)
            record(repo,s['id'],'opportunity',[*opportunity_id,'candidate_ready'],story_id=story_id,
                   family=m['family'],state='candidate_ready',replay_ms=at,evidence_ready_ms=m['evidence_ready_ms'],expires_at_ms=m['expires_at_ms'])
            if at>=m['expires_at_ms']:
                record(repo,s['id'],'opportunity',[*opportunity_id,'expired'],story_id=story_id,state='expired_archive_candidate',replay_ms=at)
            packages.append(package)
            continue
        tools=EvidenceTools(meta,messages,at,pass_id=m['pass_id'])
        if not use_model:
            package=workflow(tools,revision=revision,session_id=s['id'],force_template=True)
            if package:
                accept_package(s['id'],package,at,expected_revision=revision-1)
                packages.append(package)
            continue
        key=(s['id'],story_id,m['evidence_revision'])
        future=JOBS.get(key)
        if future is None:
            if live_attempt_blocked(s,story_id,m['evidence_revision'],at):continue
            # Never spend model calls on a new, already-expired live candidate.
            if at>=m['retention_confirmed_at_ms']+30000 or (s.get('session_mode')=='live' and at>=s['duration_ms']):
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
        elif current is None or current.get('family'):
            try:stale_package=future.result()
            except Exception:stale_package=None
            if stale_package:package_disposition(repo,s['id'],stale_package,'discarded_stale',at)
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
    if (at>=package['expires_at_ms'] or (s.get('session_mode')=='live' and (at>=s['duration_ms'] or s.get('ended_early')))) and status in ('approved','ready'):status='expired'
    published=bool(decision and decision['status']=='approved' and decision['revision']==package['revision'] and decision['package_hash']==package['package_hash'] and decision['at_ms']<=at and package['eligible_from_ms']<=at)
    return status,package if published else None

def safe_story(package,status):
    if not package:return None
    titles={}
    if package['schema_version'] in {'3.0.0','4.0.0'}:
        if package['schema_version']=='4.0.0':
            from engine.editorial_narrative import title_for
        else:
            from engine.contextual_narrative import title_for
        titles={lang:title_for(package['narrative_plan'],package['metrics'],lang) for lang in ['en','es']}
    if package['schema_version'] in {'5.0.0','6.0.0','7.0.0'}:titles={lang:display_title(package['family'],lang,package.get('renderer_version')) for lang in ['en','es']}
    m=package['metrics']
    from engine.explainability import why_now, evidence_state
    return {k:package[k] for k in ['id','revision','title','evidence_revision','eligible_from_ms','expires_at_ms']}|{'why_now':{lang:why_now(package,lang) for lang in ['en','es']},'evidence_state':evidence_state(package),'notable':bool(m.get('facts',{}).get('stands_out')),'titles':titles,'status':status,
            'family':m.get('family','pass'),'incident_id':m.get('incident_id',package['id']),
            'participants':m.get('participants',{}),'occurrence_ms':m.get('occurrence_ms',package['eligible_from_ms']),
            'selection_reason':'Priority: confirmed goals, shots, nearby pressure changes, control changes, possession, passes; newest occurrence then stable ID.'}|{k:m.get(k) for k in ['passer_id','receiver_id','team_id']}

def snapshot_data(sid,is_producer=False,story_id=None):
    with LOCK:
        s=get_session(sid);at=clock(s);meta,messages=inputs(s,at)
        packages=materialize_all(s,at) if s.get('session_mode')!='live' else [p for p in repo.list_packages(sid) if p['id'] in s.get('available_story_ids',[])]
        entries=[(p,*publication(s,p,at)) for p in packages]
        visible=[(p,status,published) for p,status,published in entries if is_producer or published]
        if not is_producer:
            grouped={}
            for entry in sorted(visible,key=lambda e:(FAMILY_PRIORITY.get(e[0].get('family','pass'),4),-e[0]['eligible_from_ms'],e[0]['id'])):
                grouped.setdefault(entry[0].get('incident_id',entry[0]['id']),entry)
            visible=sorted(grouped.values(),key=lambda e:(e[0]['metrics'].get('occurrence_ms',e[0]['eligible_from_ms']),e[0]['id']))
        selection_entries=entries if is_producer else [entry for entry in entries if entry[2]]
        selected=next((entry for entry in selection_entries if entry[0]['id']==story_id),None) if story_id else None
        if selected is None and visible:
            live_candidates=[entry for entry in visible if at<entry[0]['expires_at_ms'] and entry[1]=='ready']
            selected=min(live_candidates,key=lambda e:(FAMILY_PRIORITY.get(e[0].get('family','pass'),4),-e[0]['metrics'].get('occurrence_ms',e[0]['eligible_from_ms']),e[0]['id'])) if is_producer and live_candidates else visible[-1]
        current,status,_=selected if selected else (None,'waiting',None)
        live=[p for p,state,published in entries if published and state=='approved']
        overlay_package=min(live,key=lambda p:(FAMILY_PRIORITY.get(p.get('family','pass'),5),-p['metrics'].get('occurrence_ms',p['eligible_from_ms']),p['id'])) if live else None
        preference=s.get('overlay_preference',{})
        override=next((p for p in live if all(p[k]==preference.get(k) for k in ['id','revision','package_hash'])),None)
        if override:overlay_package=override
        elif s['match_id'] in FLAGSHIP_IDS:
            from engine.overlay_policy import choose_overlay
            overlay_package=choose_overlay(live,s.get('auto_overlay'),at)
            selected_auto={**{k:overlay_package[k] for k in ('id','revision','package_hash')},'shown_at_ms':at} if overlay_package else None
            previous=s.get('auto_overlay')
            if selected_auto and previous and all(selected_auto[k]==previous[k] for k in ('id','revision','package_hash')):selected_auto=previous
            if previous!=selected_auto:
                s['auto_overlay']=selected_auto;repo.save_session(s)
        def summary(p,state,published):
            result=safe_story(p,state)
            result['approved']=published is not None
            result['queue_state']='live' if at<p['expires_at_ms'] else 'archived'
            if p.get('family')=='possession' and not published and at>=p['expires_at_ms']:
                result['queue_state']='replaced_by_next_boundary'
            if is_producer:
                from engine.editorial import observable_decision
                result['package_hash']=p['package_hash']
                result['editorial_decision']=observable_decision(p)
            elif p.get('incident_id'):
                result['related_stories']=[safe_story(other,other_state)|{'approved':True}
                    for other,other_state,other_published in entries
                    if other_published and other['id']!=p['id'] and other.get('incident_id')==p['incident_id']]
            return result
        view=visual_snapshot(messages,at)
        audit=repo.audit(sid)
        duration=s.get('duration_ms',60000)
        return {'session_id':sid,'match_id':s['match_id'],'clock_ms':at,'duration_ms':duration,'tracking_hz':meta['tracking_hz'],
                'running':s['running'] and at<duration,'speed':s['speed'],'synthetic':True,'guided_demo':s.get('session_mode')!='live' and s['match_id'] in PRESENTATION_IDS,'flagship_demo':s['match_id'] in FLAGSHIP_IDS,
                'session_mode':s.get('session_mode','guided'),'execution':s.get('execution','ai' if FOUNDRY else 'template'),'model_identity':s.get('model_identity'),'live_status':('stopped' if s.get('ended_early') else 'complete' if at>=duration else 'ai_unavailable' if s.get('session_mode')=='live' and s.get('execution')=='ai' and not live_ai_configured() else 'running' if s['running'] else 'ready'),'last_processed_ms':s.get('last_processed_ms'),
                'workflow_attempts':live_attempt_summary(sid,at) if is_producer and s.get('session_mode')=='live' else [],
                'workflow_notices':[{'story_id':e.get('story_id'),'state':e['state'],'at_ms':e.get('replay_ms')} for e in reversed(repo.lifecycle_events(sid)) if e.get('kind')=='opportunity' and e.get('state') in {'capacity_deferred','attempt_or_session_budget_limit','ai_unavailable','expired_unscheduled'}][:8] if is_producer and s.get('session_mode')=='live' else [],
                'match_state':match_state(meta,messages,at),'score':match_state(meta,messages,at)['score'],'coverage_enabled':s.get('match_coverage',COVERAGE and s['match_id'] in MIXED_IDS),'teams':meta['teams'],'players':meta['players'],**view,
                'story':summary(current,status,selected[2]) if current else None,
                'stories':[summary(p,state,published) for p,state,published in visible],
                'approved_possession':next(({'interval':[p['metrics']['facts']['window_start_ms'],p['metrics']['facts']['window_end_ms']], 'text':p['variants'][0]['text'],'story_id':p['id']} for p,state,published in sorted(entries,key=lambda e:-e[0]['metrics'].get('occurrence_ms',0)) if published and p.get('family')=='possession'),None),
                'corrections':public_updates(repo,sid,at)[:5],
                'story_status':status,'overlay_story_id':overlay_package['id'] if overlay_package else None,
                'overlay_question':preference.get('audience_question') if override and overlay_package else None,
                'overlay_selection_reason':({'en':'Producer override of the eligible approved revision.','es':'Selección del productor entre revisiones aprobadas vigentes.'} if override else {'en':'Eligible approved stories by event priority; newest within each family. Flagship sessions hold a story for 8 s unless a goal, manual override or correction takes precedence.','es':'Historias aprobadas elegibles por prioridad; la más reciente de cada categoría. La demo principal mantiene el texto 8 s salvo gol, selección manual o corrección.'}) if overlay_package else None,
                'overlay':next(v['text'] for v in overlay_package['variants'] if v['id']=='en_simple_general') if overlay_package else None,
                'mode':current['mode'] if current else ('AI unavailable' if s.get('session_mode')=='live' and s.get('execution')=='ai' and not live_ai_configured() else 'local deterministic template' if s.get('execution')=='template' else runtime_mode()),
                'workflow_pending':any(k[0]==sid and not f.done() for k,f in JOBS.items()),
                'cursor':len(audit)*10000000+s['control_revision']*10000000+at,
                'generation':s['generation']}


from services.api.audience import create_audience_router
app.include_router(create_audience_router(lambda: repo, require, get_session, LOCK, snapshot_data,
                                         lambda s: s.get('execution')=='ai' and model_workflow_configured()))

def authorized_package(sid,story_id,token=None):
    s=get_session(sid);at=clock(s);p=materialize(s,at,story_id)
    if not p:fail(404,'story_unavailable')
    status,published=publication(s,p,at)
    if not producer(token) and not published:fail(404,'story_unavailable')
    return s,at,p,status

@app.get('/api/health')
def health():return {'workflow_ai_configured':model_workflow_configured(),'live_ai_configured':live_ai_configured(),'model_identity':{'deployment':os.getenv('FOUNDRY_MODEL_DEPLOYMENT'),'version':os.getenv('FOUNDRY_MODEL_VERSION')},'ok':True,'mode':runtime_mode(),'azure_deployed':CLOUD,'version':'0.5.0','narrative_version':'4' if STRUCTURED else '1'}

@app.get('/api/ready')
def ready():
    if CLOUD:
        repo.list_sessions()
        if transport and transport.diagnostics().get('last_error'):fail(503,'transport_not_ready')
    return {'ok':True,'persistence':'cosmos' if isinstance(repo,CosmosRepository) else 'sqlite','transport':'eventhubs' if transport else 'local','model':runtime_mode()}


@app.get('/api/matches')
def matches():return {'matches':[m for m in list_matches(COVERAGE,DEVELOPMENT) if COVERAGE or m['match_id'] not in MIXED_IDS]}


@app.post('/api/replay-sessions')
def create(body:Create,x_producer_token:str|None=Header(None)):
    require(x_producer_token)
    if body.match_id not in {m['match_id'] for m in matches()['matches']}:fail(422,'unknown_match')
    if body.execution=='ai' and not model_workflow_configured():fail(503,'model_workflow_not_configured_choose_template_or_configure_model')
    if body.mode=='live' and body.execution in {'ai','configured'} and not live_ai_configured():fail(503,'live_ai_not_configured_choose_guided_or_template')
    with LOCK:s=new_session(body.match_id,body.mode,body.execution)
    return {'session_id':s['id'],'match_id':s['match_id']}

@app.post('/api/replay-sessions/{sid}/control')
def control(sid:str,body:Control,x_producer_token:str|None=Header(None)):
    require(x_producer_token)
    with LOCK:
        s=get_session(sid)
        if body.action=='reset':
            if s.get('session_mode')=='live':
                s.update(clock_ms=clock(s),running=False,ended_early=True,updated_at=time.time(),control_revision=s['control_revision']+1);repo.save_session(s)
            fresh=new_session(s['match_id'],s.get('session_mode','guided'),s.get('execution','configured'));return {'session_id':fresh['id'],'reset_from':sid}
        if body.action=='stop':
            if s.get('session_mode')!='live':fail(409,'stop_requires_live_session')
            s.update(clock_ms=clock(s),running=False,ended_early=True,updated_at=time.time(),control_revision=s['control_revision']+1);repo.save_session(s)
            return {'session_id':sid,'running':False,'clock_ms':s['clock_ms'],'speed':1}
        if s.get('ended_early') and body.action=='start':fail(409,'simulation_ended_start_new_session')
        if s.get('session_mode')=='live' and (body.action in {'pause','seek','speed'} or body.speed is not None):fail(409,'live_match_clock_cannot_be_paused_or_sought')
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
            speed=max(.25,float(data.get('speed') or 1))
            tracking_hz=max(1,float(data.get('tracking_hz') or 10))
            interval=1/(tracking_hz*speed) if data.get('running') else .25
            await asyncio.sleep(max(.025,min(.25,interval)))
    return StreamingResponse(events(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

class OverlaySelection(Body):
    story_id:str
    expected_revision:int=Field(ge=1)
    package_hash:str=Field(min_length=64,max_length=64)
    audience_group_id:str|None=Field(default=None,max_length=100)

@app.post('/api/replay-sessions/{sid}/broadcast/director')
def broadcast_director(sid:str,x_producer_token:str|None=Header(None)):
    require(x_producer_token)
    from engine.broadcast_director import recommend, eligible_stories
    before=snapshot_data(sid,True)
    before['recent_manual_selections']=[e.get('story_id') for e in repo.lifecycle_events(sid)
        if e.get('kind')=='approval_received' and e.get('action')=='select_overlay' and e.get('story_id')][-8:]
    with LOCK:
        session=get_session(sid)
        groups=session.get('audience',{}).get('groups',[])
        wants_ai=session.get('execution')=='ai'
        has_candidates=bool(eligible_stories(before))
        attempts=session.get('broadcast_director_model_attempts',0)
        use_ai=wants_ai and model_workflow_configured() and has_candidates and attempts<12
        if use_ai:
            # Reserve before the call so retries and concurrent requests count.
            session['broadcast_director_model_attempts']=attempts+1
            repo.save_session(session)
    result=recommend(before,groups,use_ai=use_ai)
    if wants_ai and not use_ai and has_candidates:
        result['mode']='fallback'
        result['reason']=('AI recommendation limit reached. ' if attempts>=12 else 'AI is unavailable. ')+result['reason']
    # The match and its evidence can change while the model is thinking.
    # Never return a recommendation to a revision that is no longer live.
    after=snapshot_data(sid,True)
    if result['story_id'] and not any(
        s['id']==result['story_id'] and s['revision']==result['revision']
        and s.get('package_hash')==result['package_hash']
        and s.get('status') in ('ready','approved')
        and s['eligible_from_ms']<=after['clock_ms']<s['expires_at_ms']
        for s in after.get('stories',[])):
        result=recommend(after,groups,use_ai=False)
        result['mode']='fallback'
        result['reason']='The original suggestion changed while it was being evaluated. '+result['reason']
    record(repo,sid,'opportunity',[str(uuid.uuid4()),'broadcast_director'],
           state='broadcast_recommendation',story_id=result['story_id'],
           action=result['action'],mode=result['mode'],replay_ms=after['clock_ms'])
    return result

@app.post('/api/replay-sessions/{sid}/selection')
def select_overlay(sid:str,body:OverlaySelection,x_producer_token:str|None=Header(None)):
    require(x_producer_token)
    with LOCK:
        s,at,p,status=authorized_package(sid,body.story_id,x_producer_token)
        if p['revision']!=body.expected_revision or p['package_hash']!=body.package_hash:fail(409,'stale_revision')
        if status!='approved':fail(409,'approved_live_story_required')
        s['overlay_preference']={k:p[k] for k in ['id','revision','package_hash']}
        if body.audience_group_id:
            group=next((g for g in s.get('audience',{}).get('groups',[])
                        if g.get('id')==body.audience_group_id and g.get('state')!='dismissed'),None)
            if not group or not group.get('association_confirmed') or group.get('story_id')!=p['id'] or group.get('story_revision')!=p['revision'] or group.get('story_hash')!=p['package_hash']:
                fail(409,'audience_story_changed')
            question=group.get('question','').strip()
            if not question or len(question)>200:fail(409,'audience_question_unavailable')
            s['overlay_preference']['audience_question']=question
            s['overlay_preference']['audience_group_id']=body.audience_group_id
        repo.save_session(s)
        record(repo,sid,'approval_received',['overlay_selection',p['id'],p['revision'],at],story_id=p['id'],action='select_overlay',replay_ms=at)
        return {'overlay_story_id':p['id'],'selection_reason':'Producer override of deterministic selection; exact approved live revision.'}

@app.get('/api/replay-sessions/{sid}/stories/{story_id}/evidence')
def evidence(sid:str,story_id:str,x_producer_token:str|None=Header(None)):
    with LOCK:
        s,at,p,status=authorized_package(sid,story_id,x_producer_token);meta,messages=inputs(s,at)
        if p['schema_version'] in {'5.0.0','6.0.0','7.0.0'}:
            related=[]
            for other in materialize_all(s,at):
                if other['id']==p['id'] or other.get('incident_id')!=p['incident_id']:continue
                _,published=publication(s,other,at)
                if not producer(x_producer_token) and not published:continue
                related.append({'id':other['id'],'revision':other['revision'],'family':other.get('family','pass'),
                                'texts':{lang:next(v['text'] for v in other['variants'] if v['language']==lang and v['detail']=='detail' and not v['focus']) for lang in ['en','es']},
                                'source_message_ids':other['metrics']['source_message_ids'],'evidence_revision':other['evidence_revision']})
            dependencies=set(p['metrics']['source_message_ids'])
            rows=[m for m in available(messages,p['metrics']['input_cutoff_ms']) if m['message_id'] in dependencies]
            return {'story':p if producer(x_producer_token) else {k:p[k] for k in ['id','revision','title','claims','metrics','variants','evidence_revision','family','incident_id','entities']},
                    'frames':[], 'events':[m for m in rows if m['kind']=='event'],'related_stories':related,
                    'sources':[{'message_id':m['message_id'],'timeline_ms':m['timeline_ms'],'available_at_ms':m['available_at_ms'],'revision':m['revision'],'kind':m['payload']['type'] if m['kind']=='event' else 'tracking_frame','hash':digest(m)} for m in rows],
                    'cutoff_ms':p['metrics']['input_cutoff_ms'],'status':status}
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
        ended=s.get('session_mode')=='live' and (at>=s['duration_ms'] or s.get('ended_early'))
        if body.action in ('approve','edit') and (at>=p['expires_at_ms'] or ended):fail(409,'expired')
        if body.action=='approve_archive' and at<p['expires_at_ms'] and not ended:fail(409,'archive_requires_expired_candidate')
        if body.action=='retract':
            decision=repo.decision(sid,story_id)
            if not decision or decision['status']!='approved' or decision['revision']!=p['revision'] or decision['package_hash']!=p['package_hash']:
                fail(409,'not_published')
        if body.action=='edit':
            if p['schema_version'] in {'5.0.0','6.0.0','7.0.0'}:fail(422,'event_text_is_source_rendered')
            if not body.angle and (not body.text or not body.text.strip()):fail(422,'edit_text_required')
            if body.angle and not STRUCTURED:fail(422,'emphasis_requires_structured_package')
            if body.angle=='historical_contrast' and 'c-context' not in {c['id'] for c in p['claims']}:
                fail(422,'historical_contrast_requires_evidence')
            meta,messages=inputs(s,at);p=workflow(EvidenceTools(meta,messages,at,pass_id=p['metrics']['pass_id']),revision=p['revision']+1,proposed_text=body.text,session_id=sid,**({'editorial_angle':body.angle} if body.angle else {}))
            if p is None:fail(422,'review_rejected')
            new_status='ready'
        else:new_status={'approve':'approved','approve_archive':'approved','suppress':'suppressed','retract':'retracted'}[body.action]
        record(repo,sid,'approval_received',[body.idempotency_key,body.action],story_id=story_id,revision=p['revision'],action=body.action,replay_ms=at)
        result={'story_id':story_id,'status':new_status,'revision':p['revision'],'at_ms':at,'archive_only':body.action=='approve_archive','review':p['review']}
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
        start=body.from_ms if body.from_ms is not None else 0
        if start>cutoff:fail(400,'invalid_recap_interval')
        approved=[]
        for p in materialize_all(s,now):
            decision=repo.decision(sid,p['id'])
            occurrence=p['metrics'].get('occurrence_ms',p['eligible_from_ms'])
            if decision and decision['status']=='approved' and decision['revision']==p['revision'] and decision['package_hash']==p['package_hash'] and decision['at_ms']<=cutoff and p['eligible_from_ms']<=cutoff and (body.from_ms is None or start<=occurrence<=cutoff):
                approved.append(p)
        if body.focus and body.focus not in {x['id'] for x in inputs(s,now)[0]['players']+inputs(s,now)[0]['teams']}:
            fail(400,'invalid_preference')
        meta,messages=inputs(s,now)
        updates=public_updates(repo,sid,now,body.language,body.focus,start,cutoff)
        return {'title':('Resumen del segmento' if body.language=='es' else 'Segment catch-up') if s['match_id'] in MIXED_IDS else ('El partido hasta ahora' if body.language=='es' else 'Match so far'), 'match_state':match_state(meta,messages,now),
                'from_ms':start,'through_ms':cutoff,'evaluated_at_ms':now,
                'interval_rule':'Inclusive occurrence-time interval; possession windows are included by their end time. Current validity and score evaluated at evaluated_at_ms.',
                'corrections':updates[:5],'correction_count':len(updates),'mode':'approved moments only',
                **project_recap(approved,body.language,cutoff,body.focus)}

@app.get('/api/replay-sessions/{sid}/diagnostics')
def diagnostics(sid:str,x_producer_token:str|None=Header(None),story_id:str|None=None):
    require(x_producer_token)
    with LOCK:
        s=get_session(sid);at=clock(s);p=materialize(s,at,story_id);meta,messages=inputs(s,at)
        usage=p.get('model_usage',{}) if p else {}
        outcomes=repo.workflow_outcomes(sid)
        if story_id:outcomes=[o for o in outcomes if o['story_id']==story_id]
        latest=outcomes[-1] if outcomes else {}
        usage=usage or latest.get('model_usage',{})
        trace=(p.get('trace') if p and p.get('trace') else latest.get('trace',[]))
        return {'session_id':sid,'clock_ms':at,'mode':p['mode'] if p else runtime_mode(),'observations_delivered':len(available(messages,at)),'ingestion_lag_ms':max(0,at-max((m['available_at_ms'] for m in available(messages,at)),default=0)),'metric_version':'pressure-escape-v1','workflow_ms':p['workflow_ms'] if p else latest.get('workflow_ms'),'trace':trace,'audit':repo.audit(sid),'azure_deployed':CLOUD,'model_calls':p.get('model_calls',usage.get('calls',0)) if p else usage.get('calls',0),'model_tokens':p.get('model_tokens',usage.get('total_tokens',0)) if p else usage.get('total_tokens',0),'model_usage':usage,'workflow_outcomes':outcomes,'lifecycle_events':repo.lifecycle_events(sid),'decision_summary':decision_summary(p,outcomes),'transport':transport.diagnostics() if transport else {'mode':'local'},'workflow_pending':any(k[0]==sid and not f.done() for k,f in JOBS.items())}

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
