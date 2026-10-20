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
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from engine.core import available, digest, load_match, metric, visual_snapshot
from engine.repository import Repository
from engine.workflow import EvidenceTools, run_workflow

ROOT=Path(__file__).resolve().parents[2]
repo=Repository(os.getenv('WHY_NOW_DB',str(ROOT/'why_now.db')))
TOKEN=os.getenv('WHY_NOW_PRODUCER_TOKEN','local-demo-producer')
LOCK=threading.RLock()
app=FastAPI(title='WHY/NOW',version='0.1.0')
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
    meta,messages=load_match(s['match_id']); old=repo.latest_package(s['id']); m=metric(messages,at,meta)
    if not m or not m['eligible']:
        # An evidence correction can invalidate an existing publication without creating a replacement.
        if old:
            with repo.connect() as c:c.execute('UPDATE editorial SET status=? WHERE session_id=?',('superseded',s['id']))
        return None
    if old and old['evidence_revision']==m['evidence_revision']:return old
    package=run_workflow(EvidenceTools(meta,messages,at),revision=old['revision']+1 if old else 1)
    if package:
        with repo.connect() as c:
            c.execute('INSERT INTO packages VALUES (?,?,?)',(s['id'],package['revision'],json.dumps(package)))
            c.execute('UPDATE editorial SET status=? WHERE session_id=?',('superseded',s['id']))
            c.execute('INSERT INTO audit_log(session_id,action,at_ms,data) VALUES (?,?,?,?)',(s['id'],'package_ready',at,json.dumps({'revision':package['revision'],'workflow_ms':package['workflow_ms']})))
    return package

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
        s=get_session(sid);at=clock(s);meta,messages=load_match(s['match_id']); package=materialize(s,at);status,published=publication(s,package,at)
        current=package if is_producer else published
        view=visual_snapshot(messages,at)
        latest=repo.latest_package(sid)
        revision=latest['revision'] if latest else 0
        audit=repo.audit(sid)
        visible_story=safe_story(current,status)
        if visible_story and is_producer:visible_story['package_hash']=current['package_hash']
        return {'session_id':sid,'match_id':s['match_id'],'clock_ms':at,'duration_ms':60000,'running':s['running'] and at<60000,'speed':s['speed'],'synthetic':True,'score':meta['initial_state']['score'],'teams':meta['teams'],'players':meta['players'],**view,'story':visible_story,'story_status':status if is_producer or published else 'waiting','overlay':next(v['text'] for v in published['variants'] if v['id']=='en_simple_general') if published and status=='approved' else None,'mode':'local deterministic template','cursor':len(audit)*1000000+s['control_revision']*100000+at,'generation':s['generation']}

def authorized_package(sid,story_id,token=None):
    s=get_session(sid);at=clock(s); p=materialize(s,at)
    if not p or story_id!=p['id']:fail(404,'story_unavailable')
    status,published=publication(s,p,at)
    if not producer(token) and not published:fail(404,'story_unavailable')
    return s,at,p,status

@app.get('/api/health')
def health():return {'ok':True,'mode':'local deterministic template','azure_deployed':False}

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
        s,at,p,status=authorized_package(sid,story_id,x_producer_token);meta,messages=load_match(s['match_id'])
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
        with repo.connect() as c:
            old=c.execute('SELECT * FROM operations WHERE session_id=? AND operation_id=?',(sid,body.idempotency_key)).fetchone()
        if old:
            if old['request_hash']!=request_hash:fail(409,'idempotency_key_reused')
            return json.loads(old['data'])
        s,at,p,status=authorized_package(sid,story_id,x_producer_token)
        if body.expected_revision!=p['revision'] or body.package_hash!=p['package_hash']:fail(409,'stale_revision')
        if body.action in ('approve','edit') and at>=p['expires_at_ms']:fail(409,'expired')
        if body.action=='retract' and status not in ('approved','expired'):fail(409,'not_published')
        if body.action=='edit':
            if not body.text or not body.text.strip():fail(422,'edit_text_required')
            meta,messages=load_match(s['match_id']);p=run_workflow(EvidenceTools(meta,messages,at),revision=p['revision']+1,proposed_text=body.text)
            new_status='ready'
        else:new_status={'approve':'approved','suppress':'suppressed','retract':'retracted'}[body.action]
        result={'story_id':story_id,'status':new_status,'revision':p['revision'],'at_ms':at,'review':p['review']}
        with repo.connect() as c:
            if body.action=='edit':c.execute('INSERT INTO packages VALUES (?,?,?)',(sid,p['revision'],json.dumps(p)))
            c.execute('INSERT OR REPLACE INTO editorial VALUES (?,?,?,?,?)',(sid,p['revision'],new_status,at,p['package_hash']))
            c.execute('INSERT INTO audit_log(session_id,action,at_ms,data) VALUES (?,?,?,?)',(sid,body.action,at,json.dumps(result)))
            c.execute('INSERT INTO operations VALUES (?,?,?,?)',(sid,body.idempotency_key,request_hash,json.dumps(result)))
        return result

@app.post('/api/replay-sessions/{sid}/recaps')
def recap(sid:str,body:RecapRequest):
    with LOCK:
        s=get_session(sid); now=clock(s);cutoff=min(now,body.through_ms if body.through_ms is not None else now)
        meta,messages=load_match(s['match_id']);p=materialize(s,now);decision=repo.decision(sid);moments=[]
        if p and decision and decision['status']=='approved' and decision['revision']==p['revision'] and decision['package_hash']==p['package_hash'] and decision['at_ms']<=cutoff and p['eligible_from_ms']<=cutoff:
            v=next(v for v in p['variants'] if v['language']==body.language and v['detail']=='simple' and v['focus'] is None)
            moments=[{'story_id':p['id'],'revision':p['revision'],'text':v['text'],'claim_ids':v['claim_ids']}]
        return {'title':'El partido hasta ahora' if body.language=='es' else 'Match so far','through_ms':cutoff,'moments':moments,'mode':'approved moments only'}

@app.get('/api/replay-sessions/{sid}/diagnostics')
def diagnostics(sid:str,x_producer_token:str|None=Header(None)):
    require(x_producer_token)
    with LOCK:
        s=get_session(sid);at=clock(s);p=materialize(s,at);meta,messages=load_match(s['match_id'])
        return {'session_id':sid,'clock_ms':at,'mode':'local deterministic template','observations_delivered':len(available(messages,at)),'metric_version':'pressure-escape-v1','workflow_ms':p['workflow_ms'] if p else None,'trace':p['trace'] if p else [],'audit':repo.audit(sid),'azure_deployed':False,'model_calls':0,'model_cost_usd':0}
