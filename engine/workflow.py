"""Bounded local analyst/reviewer/editor workflow. This is template mode, not AI."""
from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter
import re
from engine.contracts import PublicationPackage
from engine.core import CONFIG, available, digest, metric

class ToolError(ValueError): pass

@dataclass(frozen=True)
class EvidenceTools:
    metadata: dict
    messages: list
    cutoff_ms: int
    def get_sequence(self,start_ms,end_ms):
        if start_ms<0 or end_ms>self.cutoff_ms or end_ms<start_ms or end_ms-start_ms>15000:
            raise ToolError('invalid_or_future_range')
        return [m for m in available(self.messages,self.cutoff_ms) if start_ms<=m['timeline_ms']<=end_ms][:180]
    def get_positions(self,start_ms,end_ms,player_ids=None):
        rows=[m for m in self.get_sequence(start_ms,end_ms) if m['kind']=='tracking_frame']
        if player_ids:
            if not set(player_ids).issubset({p['id'] for p in self.metadata['players']}):raise ToolError('unknown_player')
            return [{'time_ms':m['timeline_ms'],'players':[p for p in m['payload']['players'] if p['player_id'] in player_ids],'source_message_id':m['message_id']} for m in rows]
        return rows
    def compute_pass_metrics(self,pass_id='pass-1'):
        value=metric(self.messages,self.cutoff_ms,self.metadata)
        if value and value['pass_id']!=pass_id:raise ToolError('unknown_pass')
        return value
    def compare_prior_window(self,start_ms,end_ms):
        rows=self.get_sequence(start_ms,end_ms)
        return {'status':'insufficient_history','sample_count':len(rows),'reason':'One segment cannot establish sustained match control.'}
    def get_player_contribution(self,player_id):
        m=self.compute_pass_metrics()
        if player_id not in {p['id'] for p in self.metadata['players']}:raise ToolError('unknown_player')
        role='passer' if m and player_id==m['passer_id'] else 'receiver' if m and player_id==m['receiver_id'] else None
        return {'player_id':player_id,'role':role,'status':'supported' if role else 'no_relevance'}

def render_variants(m,meta):
    team=next(t['name'] for t in meta['teams'] if t['id']==m['team_id'])
    n=m['bypassed_count']; p=m['pressure_opponents_max']; d=m['progression_m']; seconds=m['retention_window_ms']//1000
    english=f'{team} passed beyond {n} opponents and kept possession as the attack moved forward.'
    spanish=f'{team} superó a {n} rivales con el pase y conservó la posesión mientras avanzaba.'
    detailed=f'Before the pass, up to {p} opponents were within {m["pressure_radius_m"]} m of the passer over a 2 s window. The pass moved beyond {n} opponents in the attacking direction. The team retained possession for {seconds} s and progressed {d:.1f} m after reception. Longitudinal positions do not prove a defensive line was broken.'
    es_detail=f'Antes del pase, hasta {p} rivales estaban a {m["pressure_radius_m"]} m del pasador en una ventana de 2 s. El pase superó a {n} rivales en dirección de ataque. El equipo conservó la posesión durante {seconds} s y avanzó {d:.1f} m después de la recepción. Las posiciones longitudinales no demuestran que se rompiera una línea defensiva.'
    base={'en_simple':english,'en_detail':detailed,'es_simple':spanish,'es_detail':es_detail}
    variants=[]
    for key,text in base.items():
        language,detail=key.split('_')
        for focus in [None]+[p['id'] for p in meta['players']]+[t['id'] for t in meta['teams']]:
            note=''
            if focus:
                if focus==m['team_id']:note=' This is the team in possession.' if language=='en' else ' Es el equipo que conserva la posesión.'
                elif focus in {t['id'] for t in meta['teams']}:note=' This team was defending the pass.' if language=='en' else ' Este equipo defendía el pase.'
                else:
                    player=next(p for p in meta['players'] if p['id']==focus)
                    if focus==m['passer_id']:note=f' {player["name"]} made the pass.' if language=='en' else f' {player["name"]} dio el pase.'
                    elif focus==m['receiver_id']:note=f' {player["name"]} received the pass and kept possession.' if language=='en' else f' {player["name"]} recibió el pase y conservó la posesión.'
                    else:note=' No direct contribution by this player is verified in this sequence.' if language=='en' else ' No hay una contribución directa verificada de este jugador en la secuencia.'
            variants.append({'id':f'{key}_{focus or "general"}','language':language,'detail':detail,'focus':focus,'text':text+note,'claim_ids':['c-pressure','c-bypass','c-retain','c-progress'],'factual_check_status':'valid'})
    return variants

def validate_variants(variants,m,meta):
    """Structural/reference/numeric validation; free-form semantics are not claimed."""
    permitted_focus={None}|{p['id'] for p in meta['players']}|{t['id'] for t in meta['teams']}
    required={(language,detail,focus) for language in ['en','es'] for detail in ['simple','detail'] for focus in permitted_focus}
    actual={(v['language'],v['detail'],v['focus']) for v in variants}
    if actual!=required or len(actual)!=len(variants):raise ValueError('variant_set_incomplete')
    names=[p['name'] for p in meta['players']]+[t['name'] for t in meta['teams']]
    for v in variants:
        text=v['text']
        for name in names:text=text.replace(name,'ENTITY')
        numbers=[float(n) for n in re.findall(r'\d+(?:\.\d+)?',text)]
        expected=[float(m['bypassed_count'])] if v['detail']=='simple' else [float(m['pressure_opponents_max']),float(m['pressure_radius_m']),2.,float(m['bypassed_count']),float(m['retention_window_ms']//1000),float(f"{m['progression_m']:.1f}")]
        if numbers!=expected:raise ValueError('variant_numeric_mismatch')
    return variants


def run_workflow(tools,revision=1,proposed_text=None):
    started=perf_counter(); trace=[]
    m=tools.compute_pass_metrics()
    if not m or not m['eligible']:return None
    trace.append({'role':'Story Analyst','action':'compute_pass_metrics','status':'supported_candidate','elapsed_ms':round((perf_counter()-started)*1000,3)})
    # Independent recomputation is allowed to narrow an edited proposal; there is one revision cycle.
    independently_checked=metric(tools.messages,tools.cutoff_ms,tools.metadata)
    if not independently_checked or independently_checked['evidence_revision']!=m['evidence_revision']:return None
    variants=validate_variants(render_variants(m,tools.metadata),m,tools.metadata)
    base=next(v['text'] for v in variants if v['id']=='en_simple_general')
    review={'status':'supported','mode':'deterministic_template','reason':'All values recomputed from delivered observations. No sustained-control or intent claim is supported.','proposed_text':proposed_text,'revised_text':base,'cycles':0}
    if proposed_text is not None and proposed_text.strip()!=base:
        tools.compare_prior_window(max(0,m['pressure_window_ms'][0]-10000),m['pressure_window_ms'][0])
        review.update(status='revised',reason='The edited wording is outside the validated factual template. Prior evidence cannot establish sustained control or intent; the reviewer restored the supported sequence description.',cycles=1)
        trace.append({'role':'Evidence Reviewer','action':'compare_prior_window','status':'needs_evidence','elapsed_ms':round((perf_counter()-started)*1000,3)})
    trace.append({'role':'Evidence Reviewer','action':'independent_metric_check','status':review['status'],'elapsed_ms':round((perf_counter()-started)*1000,3)})
    trace.append({'role':'Audience Editor','action':'render_and_validate_variants','status':'valid','variants':len(variants),'elapsed_ms':round((perf_counter()-started)*1000,3)})
    title='The pass before the moment'
    claims=[{'id':name,'type':'derived','value':value,'unit':unit,'evidence_revision':m['evidence_revision'],'source_message_ids':m['source_message_ids']} for name,value,unit in [('c-pressure',m['pressure_opponents_max'],'players'),('c-bypass',m['bypassed_count'],'players'),('c-retain',m['retention_window_ms']//1000,'s'),('c-progress',m['progression_m'],'m')]]
    package={'schema_version':'1.0.0','id':'story-pass-1','revision':revision,'title':title,'claims':claims,'metrics':m,'variants':variants,'review':review,'evidence_revision':m['evidence_revision'],'eligible_from_ms':m['available_from_ms'],'expires_at_ms':m['retention_confirmed_at_ms']+CONFIG['overlay_ttl_ms'],'trace':trace,'workflow_ms':round((perf_counter()-started)*1000,3),'mode':'local deterministic template'}
    package['package_hash']=digest(package)
    PublicationPackage.model_validate(package)
    return package
