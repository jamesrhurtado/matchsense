"""Version 1.0.0 runtime contracts. Hidden scenario labels are not part of these types."""
from __future__ import annotations
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

NonNegative=Annotated[int,Field(ge=0)]
class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
class Point(Strict):
    x_m:float=Field(ge=0,le=105,allow_inf_nan=False)
    y_m:float=Field(ge=0,le=68,allow_inf_nan=False)
class Ball(Point):
    z_m:float=Field(ge=0,allow_inf_nan=False)
    quality:Literal['simulated_observation','noisy_observation']
class Position(Point):
    player_id:str
    team_id:str
    quality:Literal['simulated_observation','noisy_observation']
class Frame(Strict):
    frame_id:str
    players:list[Position]
    missing_player_ids:list[str]
    ball:Ball|None
    ball_status:Literal['controlled','in_flight','loose','out_of_play','unknown']
    controlling_player_id:str|None
    possession_team_id:str|None
    @model_validator(mode='after')
    def coverage(self):
        ids=[p.player_id for p in self.players]
        if len(set(ids))!=len(ids) or set(ids)&set(self.missing_player_ids):raise ValueError('duplicate_or_overlapping_players')
        if self.ball_status=='in_flight' and self.controlling_player_id:raise ValueError('individual_control_during_flight')
        if self.ball_status=='controlled' and not self.controlling_player_id:raise ValueError('controlled_without_controller')
        return self
class StartDetails(Strict):
    pass_id:str
    start_position:Point
    intended_receiver_id:str|None
class EndDetails(Strict):
    pass_id:str
    outcome:Literal['received','intercepted','out_of_play','uncontrolled']
    end_position:Point
    controlling_team_id:str|None
    controlling_player_id:str|None
class PossessionDetails(Strict):
    previous_team_id:str|None
    new_team_id:str|None
    controlling_player_id:str|None
    reason:str
    incident_id:str|None=None
    pass_id:str|None=None
class PlayDetails(Strict):
    ball_status:Literal['controlled','in_flight','loose','out_of_play','unknown']
    reason:str
class EventBase(Strict):
    event_id:str
    team_id:str|None
    player_id:str|None
    possession_id:str|None
class PassStarted(EventBase):
    type:Literal['pass_started']
    details:StartDetails
class PassResolved(EventBase):
    type:Literal['pass_resolved']
    details:EndDetails
class PossessionChanged(EventBase):
    type:Literal['possession_changed']
    details:PossessionDetails
class PlayStateChanged(EventBase):
    type:Literal['play_state_changed']
    details:PlayDetails
class ShotStartDetails(Strict):
    shot_id:str=Field(min_length=1,max_length=80,pattern=r'^[A-Za-z0-9_-]+$')
    location:Point|None=None
class ShotEndDetails(ShotStartDetails):
    outcome:Literal['goal','saved','blocked','off_target','unknown']
class GoalDetails(Strict):
    goal_id:str=Field(min_length=1,max_length=80,pattern=r'^[A-Za-z0-9_-]+$')
    status:Literal['pending','confirmed','cancelled']
    scorer_id:str|None=None
    shot_id:str|None=None
    own_goal:bool=False
class RecoveryDetails(Strict):
    incident_id:str=Field(min_length=1,max_length=80,pattern=r'^[A-Za-z0-9_-]+$')
    previous_team_id:str|None
    cause:Literal['tackle','interception','loose_ball','unknown']='unknown'
    pass_id:str|None=None
class PeriodDetails(Strict):
    status:Literal['started','ended']
class ShotStarted(EventBase):
    team_id:str=Field(min_length=1)
    type:Literal['shot_started']
    details:ShotStartDetails
class ShotResolved(EventBase):
    team_id:str=Field(min_length=1)
    type:Literal['shot_resolved']
    details:ShotEndDetails
class GoalStatusChanged(EventBase):
    team_id:str=Field(min_length=1)
    type:Literal['goal_status_changed']
    details:GoalDetails
class BallRecovered(EventBase):
    team_id:str=Field(min_length=1)
    type:Literal['ball_recovered']
    details:RecoveryDetails
class PeriodStateChanged(EventBase):
    type:Literal['period_state_changed']
    details:PeriodDetails
EventPayload=Annotated[PassStarted|PassResolved|PossessionChanged|PlayStateChanged|ShotStarted|ShotResolved|GoalStatusChanged|BallRecovered|PeriodStateChanged,Field(discriminator='type')]
class Envelope(Strict):
    schema_version:Literal['1.0.0']
    match_id:str
    message_id:str
    sequence_no:NonNegative
    timeline_ms:NonNegative
    period:int=Field(ge=1)
    period_elapsed_ms:NonNegative
    available_at_ms:NonNegative
    revision:int=Field(ge=1)
    supersedes_message_id:str|None
    @model_validator(mode='after')
    def temporal(self):
        if self.available_at_ms<self.timeline_ms:raise ValueError('availability_before_occurrence')
        if self.revision>1 and self.supersedes_message_id is None:raise ValueError('missing_correction_lineage')
        return self
class EventObservation(Envelope):
    kind:Literal['event']
    payload:EventPayload
class TrackingObservation(Envelope):
    kind:Literal['tracking_frame']
    payload:Frame
Observation=Annotated[EventObservation|TrackingObservation,Field(discriminator='kind')]
OBSERVATION=TypeAdapter(Observation)
class Team(Strict):
    id:str
    name:str
    color:str
class Player(Strict):
    id:str
    team_id:str
    name:str
    number:int=Field(ge=1,le=99)
    role:str
class Pitch(Strict):
    length_m:Literal[105]
    width_m:Literal[68]
    convention:Literal['x right, y down']
class Period(Strict):
    period:int=Field(ge=1)
    timeline_offset_ms:NonNegative
    attack_direction:dict[str,Literal['right','left']]
class InitialState(Strict):
    period:int
    period_elapsed_ms:NonNegative
    score:dict[str,NonNegative]
    active_player_ids:list[str]
    ball_status:str
    possession_team_id:str|None
class MatchMetadata(Strict):
    schema_version:Literal['1.0.0']
    match_id:str
    synthetic:Literal[True]
    scope:Literal['segment','full_match']
    pitch:Pitch
    teams:list[Team]=Field(min_length=2,max_length=2)
    players:list[Player]
    periods:list[Period]
    initial_state:InitialState
    tracking_hz:float=Field(gt=0,le=100)
    provenance_id:str

class Claim(Strict):
    id:Literal['c-pressure','c-bypass','c-retain','c-progress']
    type:Literal['derived']
    value:float=Field(allow_inf_nan=False)
    unit:Literal['players','s','m']
    evidence_revision:str
    source_message_ids:list[str]=Field(min_length=1)
class AudienceVariant(Strict):
    id:str
    language:Literal['en','es']
    detail:Literal['simple','detail']
    focus:str|None
    text:str=Field(min_length=1,max_length=2000)
    claim_ids:list[str]=Field(min_length=1)
    factual_check_status:Literal['valid']
class ReviewDecision(Strict):
    status:Literal['supported','revised']
    mode:Literal['deterministic_template','foundry','template_fallback']
    reason:str
    proposed_text:str|None
    revised_text:str
    cycles:int=Field(ge=0,le=1)
class ModelUsage(Strict):
    calls:int=Field(ge=0)
    input_tokens:int=Field(ge=0)
    output_tokens:int=Field(ge=0)
    total_tokens:int=Field(ge=0)
    usage_complete:bool

class EvidenceClaim(Strict):
    id:str=Field(pattern=r'^c-[a-z-]+$')
    type:Literal['scoped_fact']
    predicate:Literal['nearby_opponents','longitudinal_bypass','team_retained','team_progression','forward_pass_displacement','reception_zone','pass_reception','pass_release','previous_pass_comparison']
    subject_id:str
    subject_name:str
    value:float|str
    unit:Literal['players','s','m','zone','player']
    evidence_revision:str
    source_message_ids:list[str]=Field(min_length=1)
    window_start_ms:NonNegative
    window_end_ms:NonNegative
    input_cutoff_ms:NonNegative
    coverage:float=Field(ge=0,le=1)
    qualification:str

class PassComparator(Strict):
    pass_id:str
    release_ms:NonNegative
    resolution_ms:NonNegative
    forward_m:float=Field(allow_inf_nan=False)
    release_position:Point
    reception_position:Point
    source_message_ids:list[str]=Field(min_length=2,max_length=2)
    source_hashes:list[str]=Field(min_length=2,max_length=2)

class RecentPassContext(Strict):
    version:Literal['recent-completed-three-v1']
    current_pass_id:str
    team_id:str
    attack_direction:Literal['left','right']
    period:int=Field(ge=1)
    release_ms:NonNegative
    window_start_ms:NonNegative
    lookback_ms:Literal[120000]
    cutoff_ms:NonNegative
    status:Literal['available','incomplete_history','insufficient_history']
    sample_count:int=Field(ge=0,le=3)
    comparators:list[PassComparator]=Field(max_length=3)
    current_forward_m:float|None=Field(allow_inf_nan=False)
    unit:Literal['m']
    relation:Literal['greater_than_each','no_comparative_claim']
    source_message_ids:list[str]=Field(min_length=2)
    source_hashes:list[str]=Field(min_length=2)
    coverage_complete:bool
    limitation:str
    revision:str=Field(pattern=r'^[a-f0-9]{16}$')
    @model_validator(mode='after')
    def population(self):
        if self.sample_count!=len(self.comparators):raise ValueError('context_sample_count_mismatch')
        if len(self.source_message_ids)!=len(self.source_hashes):raise ValueError('context_sources_mismatch')
        if len(set(self.source_message_ids))!=len(self.source_message_ids):raise ValueError('context_sources_mismatch')
        if self.window_start_ms>self.release_ms or self.cutoff_ms<self.release_ms:raise ValueError('context_window_mismatch')
        if sorted(self.comparators,key=lambda p:(-p.resolution_ms,p.pass_id))!=self.comparators:
            raise ValueError('context_order_mismatch')
        if any(p.release_ms>=p.resolution_ms or not self.window_start_ms<=p.resolution_ms<self.release_ms
               or p.pass_id==self.current_pass_id or not set(p.source_message_ids)<=set(self.source_message_ids)
               for p in self.comparators):raise ValueError('context_population_mismatch')
        sign=1 if self.attack_direction=='right' else -1
        hashes=dict(zip(self.source_message_ids,self.source_hashes))
        if any(p.forward_m!=sign*(p.reception_position.x_m-p.release_position.x_m) or
               p.source_hashes!=[hashes[mid] for mid in p.source_message_ids]
               for p in self.comparators):raise ValueError('context_measurement_mismatch')
        return self

class NarrativePlan(Strict):
    angle:Literal['progression','reception','proximity','historical_contrast']
    simple_claim_ids:list[str]=Field(min_length=2,max_length=3)
    detail_claim_ids:list[str]=Field(min_length=4,max_length=9)

class AudienceClause(Strict):
    id:str
    claim_ids:list[str]
    text:str

class StructuredVariant(AudienceVariant):
    clauses:list[AudienceClause]=Field(min_length=1)

class PublicationPackage(Strict):
    schema_version:Literal['1.0.0','2.0.0','3.0.0','4.0.0']
    id:str
    revision:int=Field(ge=1)
    title:str
    claims:list[Claim|EvidenceClaim]=Field(min_length=1)
    metrics:dict
    variants:list[StructuredVariant|AudienceVariant]
    review:ReviewDecision
    evidence_revision:str
    eligible_from_ms:NonNegative
    expires_at_ms:NonNegative
    trace:list[dict]
    workflow_ms:float=Field(ge=0)
    mode:Literal['local deterministic template','Microsoft Agent Framework + Azure OpenAI','template fallback']
    model_usage:ModelUsage|None=None
    narrative_plan:NarrativePlan|None=None
    renderer_version:str|None=None
    package_hash:str
    @model_validator(mode='after')
    def consistent_references(self):
        claim_ids={c.id for c in self.claims}
        if len(claim_ids)!=len(self.claims):raise ValueError('duplicate_claim')
        if any(c.evidence_revision!=self.evidence_revision for c in self.claims):raise ValueError('claim_revision_mismatch')
        if len({v.id for v in self.variants})!=len(self.variants):raise ValueError('duplicate_variant')
        if any(not set(v.claim_ids).issubset(claim_ids) for v in self.variants):raise ValueError('unknown_claim_reference')
        if self.schema_version=='2.0.0':
            if not self.narrative_plan or self.renderer_version!='claim-blocks-v2':raise ValueError('missing_narrative_plan')
            if not all(isinstance(c,EvidenceClaim) for c in self.claims):raise ValueError('unscoped_claim')
            if not all(isinstance(v,StructuredVariant) for v in self.variants):raise ValueError('unbound_variant')
            from engine.narrative import validate_realization
            validate_realization(self.model_dump())
        if self.schema_version=='3.0.0':
            if not self.narrative_plan or self.renderer_version!='context-claims-v3':raise ValueError('missing_narrative_plan')
            if not all(isinstance(c,EvidenceClaim) for c in self.claims):raise ValueError('unscoped_claim')
            if not all(isinstance(v,StructuredVariant) for v in self.variants):raise ValueError('unbound_variant')
            from engine.contextual_narrative import validate_realization
            validate_realization(self.model_dump())
        if self.schema_version=='4.0.0':
            if not self.narrative_plan or self.renderer_version!='editorial-claims-v4':raise ValueError('missing_narrative_plan')
            if not all(isinstance(c,EvidenceClaim) for c in self.claims):raise ValueError('unscoped_claim')
            if not all(isinstance(v,StructuredVariant) for v in self.variants):raise ValueError('unbound_variant')
            from engine.editorial_narrative import validate_realization
            validate_realization(self.model_dump())
        return self
