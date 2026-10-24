"""v5 deterministic bilingual realization. Only bounded fact ordering is model-owned."""
from copy import deepcopy
from time import perf_counter
from typing import Literal
from pydantic import Field, model_validator
from engine.contracts import Strict, AudienceVariant, ReviewDecision, ModelUsage, Point, NonNegative
from engine.core import digest

LABELS={'shot':('Shot outcome','Resultado del remate'),'goal':('Confirmed goal','Gol confirmado'),
        'possession':('Possession · segment window','Posesión · intervalo del segmento'),'recovery':('Change of control','Cambio de control'),'pressure':('Pressure Swing','Cambio de presión cercana')}


def render(m,meta,lang,detail='simple',focus=None):
    es=lang=='es';f=m['facts']
    names={p['id']:p['name'] for p in meta['players']+meta['teams']}
    team=names.get(m['team_id'],'');roles=m['participants'];actor=next((names.get(v) for v in roles.values() if v),None)
    if m['family']=='shot':
        who=actor or (f'Jugador sin identificar de {team}' if es else f'Unidentified {team} player')
        outcomes={'saved':('saved','atajado'),'blocked':('blocked','bloqueado'),'off_target':('off target','fuera de portería'),
                  'unknown':('outcome unconfirmed','resultado sin confirmar'),'goal':('goal confirmed','gol confirmado')}
        outcome=outcomes[f['outcome']][int(es)]
        text=f'{who}: remate {outcome}.' if es else f'{who}: shot {outcome}.'
        if f.get('goal_status')=='cancelled':text+= ' El gol fue anulado.' if es else ' The goal was cancelled.'
        if detail=='detail':text+= (' Resultado observado; no indica la calidad de la ocasión.' if es else ' Observed outcome; this does not rate chance quality.')
    elif m['family']=='goal':
        text=f'Gol confirmado para {team}.' if es else f'Confirmed goal for {team}.'
        if actor:text+= (f' Autogol de {actor}.' if es else f' Own goal by {actor}.') if f['own_goal'] else (f' Autor: {actor}.' if es else f' Scorer: {actor}.')
        else:text+= ' Autor sin identificar.' if es else ' Scorer unidentified.'
        if detail=='detail':text+= ' Sin atribución de asistencia.' if es else ' No assist attribution is established.'
    elif m['family']=='recovery':
        previous=names.get(f['previous_team_id'])
        if f['kind']=='recovery':text=(f'{actor or team} recuperó el balón.' if es else f'{actor or team} recovered the ball.')
        elif f['kind']=='restart':text=(f'{team} tiene el control en la reanudación.' if es else f'{team} has control at the restart.')
        else:text=(f'El control pasó de {previous} a {team}.' if es else f'Control changed from {previous} to {team}.')
        if f['sustained']:text+= ' Conservó la posesión durante los 3 s siguientes.' if es else ' The team retained possession for the next 3 s.'
        if detail=='detail':
            causes={'tackle':('Observed tackle.','Entrada observada.'),'interception':('Observed interception.','Intercepción observada.'),'loose_ball':('Observed loose-ball acquisition.','Recuperación de balón suelto observada.'),'unknown':('Cause unverified.','Causa sin verificar.')}
            text+=' '+causes[f['cause']][int(es)]
    elif m['family']=='pressure':
        passer=names[roles['passer']];receiver=names[roles['receiver']]
        b=f['before']['mean'];a=f['after']['mean']
        if detail=='simple':
            text=(f'{passer} pasó {f["forward_m"]:.1f} m hacia delante a {receiver}. La media de rivales cercanos pasó de {b:.1f} antes del pase a {a:.1f} tras la recepción.' if es else f'{passer} passed {f["forward_m"]:.1f} m forward to {receiver}. Average nearby opponents fell from {b:.1f} before the pass to {a:.1f} after reception.')
        else:
            text=(f'Análisis: radio {f["radius_m"]} m; medias ponderadas por tiempo {b:.1f} → {a:.1f} rivales; descenso {f["drop"]:.1f}. Ventanas de 2 s antes del pase y 2 s desde la recepción; cobertura {min(f["before"]["coverage"],f["after"]["coverage"])*100:.1f}%. Pase {f["forward_m"]:.1f} m hacia delante; posesión del equipo confirmada durante 3 s.' if es else f'Analyst: {f["radius_m"]} m radius; time-weighted means {b:.1f} → {a:.1f} opponents; drop {f["drop"]:.1f}. Windows: 2 s before release and 2 s from reception; coverage {min(f["before"]["coverage"],f["after"]["coverage"])*100:.1f}%. Pass {f["forward_m"]:.1f} m forward; team possession confirmed for 3 s.')
        if f['stands_out']:
            text+=(' Avanzó más que cada uno de los tres pases completados anteriores del equipo en esta repetición.' if es else ' It travelled farther forward than each of the team’s previous three completed passes in this replay.')
        if focus==roles['passer']:text=(f'Pase de {passer}. ' if es else f'Passer: {passer}. ')+text
        elif focus==roles['receiver']:text=(f'Recepción de {receiver}. ' if es else f'Receiver: {receiver}. ')+text
        text+=(' La proximidad no demuestra intención ni causalidad táctica.' if es else ' Proximity does not establish tactical intent or causation.')
    else:
        def clock(ms):return f'{ms//60000:02}:{ms//1000%60:02}'
        interval=f'{clock(f["window_start_ms"])}–{clock(f["window_end_ms"])}'
        text=(f'Posesión en {interval}: ' if es else f'Possession in {interval}: ')
        if f['percentages'] is None:text+= 'evidencia insuficiente para porcentajes.' if es else 'insufficient evidence for percentages.'
        else:text+= ', '.join(f'{names[t]} {v:.1f}%' for t,v in f['percentages'].items())+'.'
        # Denominator and coverage are mandatory even in simple text.
        text+=(f' Base: {f["assigned_ms"]/1000:g} s asignados; cobertura {f["coverage"]*100:.1f}%.' if es else f' Denominator: {f["assigned_ms"]/1000:g} s assigned; coverage {f["coverage"]*100:.1f}%.')
        text+=(f' Fuera de juego {f["dead_ms"]/1000:g} s, suelto {f["loose_ms"]/1000:g} s, desconocido {f["unknown_ms"]/1000:g} s.' if es else f' Dead {f["dead_ms"]/1000:g} s, loose {f["loose_ms"]/1000:g} s, unknown {f["unknown_ms"]/1000:g} s.')
        text+=' Solo este intervalo.' if es else ' This segment window only.'
    relevant={m['team_id']}|set(roles.values())
    if m['family']=='possession':relevant=set(f['team_ms'])
    if focus and focus not in relevant:text+= ' Sin participación verificada en este evento.' if es else ' No verified involvement in this event.'
    return text


class EventClaim(Strict):
    id:Literal['c-event']='c-event'
    predicate:Literal['shot_outcome','confirmed_goal','control_transition','possession_interval','pressure_swing']
    value:dict
    unit:Literal['observation']='observation'
    evidence_revision:str
    source_message_ids:list[str]=Field(min_length=1)


class ShotFacts(Strict):
    outcome:Literal['goal','saved','blocked','off_target','unknown']
    reported_outcome:Literal['goal','saved','blocked','off_target','unknown']
    goal_status:Literal['pending','confirmed','cancelled']|None
    location:Point|None

class GoalFacts(Strict):
    status:Literal['confirmed']
    own_goal:bool
    score:dict[str,NonNegative]
    score_before:dict[str,NonNegative]
    shot_id:str|None

class RecoveryFacts(Strict):
    previous_team_id:str|None
    new_team_id:str
    cause:Literal['tackle','interception','loose_ball','unknown']
    kind:Literal['recovery','control_change','restart']
    sustained:bool

class PossessionFacts(Strict):
    window_start_ms:NonNegative
    window_end_ms:NonNegative
    team_ms:dict[str,NonNegative]
    assigned_ms:NonNegative
    unknown_ms:NonNegative
    dead_ms:NonNegative
    loose_ms:NonNegative
    coverage:float=Field(ge=0,le=1)
    percentages:dict[str,float]|None
    status:Literal['available','insufficient_evidence']
    period:int=Field(ge=1)
    source_message_ids:list[str]
    source_hashes:list[str]
    input_cutoff_ms:NonNegative
    @model_validator(mode='after')
    def accounting(self):
        if sum(self.team_ms.values())!=self.assigned_ms:raise ValueError('possession_denominator_mismatch')
        if self.assigned_ms+self.unknown_ms+self.dead_ms+self.loose_ms!=self.window_end_ms-self.window_start_ms:raise ValueError('possession_interval_mismatch')
        expected=self.assigned_ms/(self.assigned_ms+self.unknown_ms) if self.assigned_ms+self.unknown_ms else 0
        if self.coverage!=expected:raise ValueError('possession_coverage_mismatch')
        enough=self.assigned_ms>=30000 and self.coverage>=.95
        if (self.percentages is not None)!=enough or (self.status=='available')!=enough:raise ValueError('unsupported_possession_percentages')
        if enough and self.percentages!={t:v/self.assigned_ms*100 for t,v in self.team_ms.items()}:raise ValueError('possession_percentage_mismatch')
        return self

class ProximityWindow(Strict):
    start_ms:NonNegative
    end_ms:NonNegative
    known_ms:NonNegative
    coverage:float=Field(ge=.95,le=1)
    mean:float=Field(ge=0,allow_inf_nan=False)
    @model_validator(mode='after')
    def accounting(self):
        if self.end_ms-self.start_ms!=2000 or self.known_ms>2000 or self.coverage!=self.known_ms/2000:raise ValueError('pressure_window_mismatch')
        return self

class PressureComparator(Strict):
    pass_id:str
    forward_m:float=Field(allow_inf_nan=False)
    resolution_ms:NonNegative

class PressureFacts(Strict):
    before:ProximityWindow
    after:ProximityWindow
    radius_m:Literal[6]
    drop:float=Field(ge=1,allow_inf_nan=False)
    forward_m:float=Field(ge=10,allow_inf_nan=False)
    pass_id:str
    release_ms:NonNegative
    reception_ms:NonNegative
    retained_ms:Literal[3000]
    retained_progression_m:float=Field(ge=5,allow_inf_nan=False)
    comparators:list[PressureComparator]=Field(max_length=3)
    comparison_status:Literal['available','incomplete_history','insufficient_history']
    stands_out:bool
    @model_validator(mode='after')
    def supported(self):
        if self.before.mean<1 or self.drop!=self.before.mean-self.after.mean:raise ValueError('pressure_drop_mismatch')
        if self.before.end_ms!=self.release_ms or self.after.start_ms!=self.reception_ms or self.reception_ms<=self.release_ms:raise ValueError('pressure_interval_mismatch')
        if self.comparison_status=='available' and len(self.comparators)!=3:raise ValueError('pressure_population_mismatch')
        if len({c.pass_id for c in self.comparators})!=len(self.comparators) or any(not max(0,self.release_ms-120000)<=c.resolution_ms<self.release_ms for c in self.comparators):raise ValueError('pressure_population_scope')
        expected=self.comparison_status=='available' and len(self.comparators)==3 and all(self.forward_m>c.forward_m for c in self.comparators)
        if self.stands_out!=expected:raise ValueError('pressure_comparison_mismatch')
        return self

class EventEvidence(Strict):
    family:Literal['shot','goal','recovery','possession','pressure']
    subject_id:str
    incident_id:str
    team_id:str|None
    participants:dict[str,str|None]
    occurrence_ms:NonNegative
    evidence_ready_ms:NonNegative
    input_cutoff_ms:NonNegative
    window_start_ms:NonNegative
    window_end_ms:NonNegative
    source_message_ids:list[str]=Field(min_length=1)
    source_hashes:list[str]=Field(min_length=1)
    facts:dict
    eligible:Literal[True]
    definition_version:Literal['match-events-v1','nearby-pressure-swing-v1']
    expires_at_ms:NonNegative
    evidence_revision:str=Field(pattern=r'^[a-f0-9]{16}$')
    @model_validator(mode='after')
    def scope(self):
        fact_types={'shot':ShotFacts,'goal':GoalFacts,'recovery':RecoveryFacts,'possession':PossessionFacts,'pressure':PressureFacts}
        fact_types[self.family].model_validate(self.facts)
        if (self.family=='pressure')!=(self.definition_version=='nearby-pressure-swing-v1'):raise ValueError('event_definition_mismatch')
        roles={'shot':{'shooter'},'goal':{'scorer'},'recovery':{'recovering_player'},'possession':set(),'pressure':{'passer','receiver'}}
        if set(self.participants)!=roles[self.family]:raise ValueError('unsupported_participant_role')
        if len(set(self.source_message_ids))!=len(self.source_message_ids) or len(self.source_message_ids)!=len(self.source_hashes):raise ValueError('event_dependencies_mismatch')
        if self.window_start_ms>self.window_end_ms or self.window_end_ms>self.input_cutoff_ms or self.evidence_ready_ms>self.expires_at_ms:raise ValueError('event_time_mismatch')
        if digest(self.model_dump(exclude={'evidence_revision'}))[:16]!=self.evidence_revision:raise ValueError('event_fingerprint_mismatch')
        return self


class EventPackage(Strict):
    schema_version:Literal['5.0.0','6.0.0']='5.0.0'
    id:str
    revision:int=Field(ge=1)
    title:str
    family:Literal['shot','goal','recovery','possession','pressure']
    incident_id:str
    claims:list[EventClaim]=Field(min_length=1,max_length=1)
    metrics:EventEvidence
    variants:list[AudienceVariant]
    review:ReviewDecision
    evidence_revision:str
    eligible_from_ms:int=Field(ge=0)
    expires_at_ms:int=Field(ge=0)
    trace:list[dict]
    workflow_ms:float=Field(ge=0)
    mode:Literal['local deterministic template','template fallback','Microsoft Agent Framework + Azure OpenAI']
    model_usage:ModelUsage
    renderer_version:Literal['match-events-v5','pressure-swing-v6']='match-events-v5'
    # Only names/roster used for deterministic realization; no evaluation labels.
    entities:dict
    package_hash:str
    @model_validator(mode='after')
    def realization(self):
        p=self.model_dump();m=p['metrics']
        if (self.family=='pressure')!=(self.schema_version=='6.0.0') or (self.family=='pressure')!=(self.renderer_version=='pressure-swing-v6'):raise ValueError('event_schema_mismatch')
        if self.family!=m['family'] or self.incident_id!=m['incident_id']:raise ValueError('event_scope_mismatch')
        if self.id!=story_id(m) or self.evidence_revision!=m['evidence_revision']:raise ValueError('event_identity_mismatch')
        predicate={'shot':'shot_outcome','goal':'confirmed_goal','recovery':'control_transition','possession':'possession_interval','pressure':'pressure_swing'}[self.family]
        if self.claims[0].predicate!=predicate or self.claims[0].value!=m['facts'] or self.claims[0].evidence_revision!=self.evidence_revision or self.claims[0].source_message_ids!=m['source_message_ids']:raise ValueError('unsupported_event_claim')
        expected=variants(m,self.entities)
        if p['variants']!=expected:raise ValueError('unsupported_event_realization')
        if self.title!=LABELS[self.family][0] or self.eligible_from_ms!=m['evidence_ready_ms'] or self.expires_at_ms!=m['expires_at_ms']:raise ValueError('event_publication_mismatch')
        if digest({k:v for k,v in p.items() if k!='package_hash'})!=self.package_hash:raise ValueError('event_hash_mismatch')
        return self


def story_id(m):return f'story-{m["family"]}-{m["subject_id"]}'


def variants(m,meta):
    return [{'id':f'{lang}_{detail}_{focus or "general"}','language':lang,'detail':detail,'focus':focus,
             'text':render(m,meta,lang,detail,focus),'claim_ids':['c-event'],'factual_check_status':'valid'}
            for lang in ['en','es'] for detail in ['simple','detail'] for focus in [None]+[p['id'] for p in meta['players']+meta['teams']]]


def build_event_package(m,meta,revision=1):
    start=perf_counter();entities={k:meta[k] for k in ['players','teams']}
    predicate={'shot':'shot_outcome','goal':'confirmed_goal','recovery':'control_transition','possession':'possession_interval','pressure':'pressure_swing'}[m['family']]
    vs=variants(m,entities)
    p={'schema_version':'6.0.0' if m['family']=='pressure' else '5.0.0','id':story_id(m),'revision':revision,'title':LABELS[m['family']][0],
       'family':m['family'],'incident_id':m['incident_id'],'metrics':deepcopy(m),
       'claims':[{'id':'c-event','predicate':predicate,'value':deepcopy(m['facts']),'unit':'observation','evidence_revision':m['evidence_revision'],'source_message_ids':m['source_message_ids']}],
       'variants':vs,'review':{'status':'supported','mode':'deterministic_template','reason':('Source facts rendered in the bounded v6 pressure grammar; producer approval required.' if m['family']=='pressure' else 'Source facts rendered in the bounded v5 grammar; producer approval required.'), 'proposed_text':None,'revised_text':vs[0]['text'],'cycles':0},
       'evidence_revision':m['evidence_revision'],'eligible_from_ms':m['evidence_ready_ms'],'expires_at_ms':m['expires_at_ms'],
       'trace':[{'role':'Claim Reviewer','action':'validate_event_facts','status':'supported','elapsed_ms':0}],
       'workflow_ms':(perf_counter()-start)*1000,'mode':'local deterministic template',
       'model_usage':{'calls':0,'input_tokens':0,'output_tokens':0,'total_tokens':0,'usage_complete':True},
       'renderer_version':'pressure-swing-v6' if m['family']=='pressure' else 'match-events-v5','entities':entities}
    p['package_hash']=digest(p);EventPackage.model_validate(p);return p


def read_package(value):
    if value.get('schema_version') in {'5.0.0','6.0.0'}:return EventPackage.model_validate(value)
    from engine.contracts import PublicationPackage
    return PublicationPackage.model_validate(value)
