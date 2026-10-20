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
EventPayload=Annotated[PassStarted|PassResolved|PossessionChanged|PlayStateChanged,Field(discriminator='type')]
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
    mode:Literal['deterministic_template']
    reason:str
    proposed_text:str|None
    revised_text:str
    cycles:int=Field(ge=0,le=1)
class PublicationPackage(Strict):
    schema_version:Literal['1.0.0']
    id:str
    revision:int=Field(ge=1)
    title:str
    claims:list[Claim]=Field(min_length=1)
    metrics:dict
    variants:list[AudienceVariant]
    review:ReviewDecision
    evidence_revision:str
    eligible_from_ms:NonNegative
    expires_at_ms:NonNegative
    trace:list[dict]
    workflow_ms:float=Field(ge=0)
    mode:Literal['local deterministic template']
    package_hash:str
    @model_validator(mode='after')
    def consistent_references(self):
        claim_ids={c.id for c in self.claims}
        if len(claim_ids)!=len(self.claims):raise ValueError('duplicate_claim')
        if any(c.evidence_revision!=self.evidence_revision for c in self.claims):raise ValueError('claim_revision_mismatch')
        if len({v.id for v in self.variants})!=len(self.variants):raise ValueError('duplicate_variant')
        if any(not set(v.claim_ids).issubset(claim_ids) for v in self.variants):raise ValueError('unknown_claim_reference')
        return self
