"""Deterministic projection over authorized approved revisions only.

Signature v1: predicate + subject + comparison relation + measurement bucket.
Metres use floor(value / 10): 9.9 -> 0, 10 -> 1, -0.1 -> -1. Seconds and
player counts stay exact; zones stay categorical. Similarity is never a trend.
"""
import math
from engine.core import digest
from engine.contextual_narrative import title_for
from engine.editorial_narrative import title_for as editorial_title

RECAP_VERSION = 'distinct-approved-v1'


def project_recap(packages, language, cutoff, focus=None):
    if any(p.get('schema_version') in {'5.0.0','6.0.0'} for p in packages):
        return mixed_recap(packages,language,cutoff,focus)
    relevant = [p for p in packages if not focus or focus in
                {p['metrics']['team_id'], p['metrics']['passer_id'], p['metrics']['receiver_id']}]
    groups = {}
    inputs = []
    for package in sorted(relevant, key=lambda p: (p['eligible_from_ms'], p['id'])):
        metrics = package['metrics']
        variant = next(v for v in package['variants'] if v['language'] == language and
                       v['detail'] == 'simple' and v['focus'] == focus)
        claims = {c['id']: c for c in package['claims']}
        signature = []
        for cid in variant['claim_ids']:
            claim = claims[cid]
            value = claim['value']
            if claim['unit'] == 'm':
                value = math.floor(value / 10)
            signature.append((claim.get('predicate', cid), claim.get('subject_id', metrics['team_id']),
                              metrics.get('context', {}).get('relation') if cid == 'c-context' else None, value))
        key = digest(signature)
        inputs.append({'story_id': package['id'], 'revision': package['revision'], 'package_hash': package['package_hash']})
        member = {'story_id': package['id'], 'revision': package['revision'], 'at_ms': package['eligible_from_ms']}
        if key in groups:
            groups[key]['similar_moments'].append(member)
            continue
        groups[key] = {'story_id': package['id'], 'revision': package['revision'],
                       'title': (editorial_title if package['schema_version']=='4.0.0' else title_for)(package['narrative_plan'], metrics, language) if package['schema_version'] in {'3.0.0','4.0.0'} else package['title'],
                       'text': variant['text'], 'claim_ids': variant['claim_ids'], 'at_ms': package['eligible_from_ms'],
                       'archived': cutoff >= package['expires_at_ms'], 'similar_moments': [member],
                       'selection_reason': 'First approved moment with this fact signature; newest three distinct signatures retained.',
                       'evidence_path': f'/stories/{package["id"]}/evidence'}
    moments = sorted(groups.values(), key=lambda m: (m['at_ms'], m['story_id']))[-3:]
    return {'selection_rule_version': RECAP_VERSION, 'input_revisions': inputs, 'projection_hash': digest([RECAP_VERSION, inputs, language, focus]),
            'moments': moments, 'approved_count': len(relevant), 'distinct_count': len(groups)}


def mixed_recap(packages,language,cutoff,focus=None):
    from engine.event_metrics import FAMILY_PRIORITY
    from engine.event_narrative import LABELS
    def relevant(p):
        m=p['metrics']
        return not focus or focus in ({m.get('team_id'),m.get('passer_id'),m.get('receiver_id')}|set(m.get('participants',{}).values())| (set(m['facts']['team_ms']) if m.get('family')=='possession' else set()))
    relevant_packages=[p for p in packages if relevant(p)]
    incidents={};inputs=[]
    for p in sorted(relevant_packages,key=lambda p:(FAMILY_PRIORITY.get(p.get('family','pass'),5),-p['metrics'].get('occurrence_ms',p['eligible_from_ms']),p['id'])):
        inputs.append({k:p[k] for k in ['id','revision','package_hash']})
        key='possession' if p.get('family')=='possession' else p.get('incident_id',p['id'])
        incidents.setdefault(key,p)
    # Goals first, then one from each remaining family per round; no invented variety.
    goals=sorted([p for p in incidents.values() if p.get('family')=='goal'],key=lambda p:(p['eligible_from_ms'],p['id']),reverse=True)
    buckets={f:sorted([p for p in incidents.values() if p.get('family','pass')==f],key=lambda p:(p['eligible_from_ms'],p['id']),reverse=True) for f in ['shot','pressure','recovery','possession','pass']}
    chosen=goals[:5]
    while len(chosen)<5 and any(buckets.values()):
        for rows in buckets.values():
            if rows and len(chosen)<5:chosen.append(rows.pop(0))
    moments=[]
    for p in sorted(chosen,key=lambda p:(p['metrics'].get('occurrence_ms',p['eligible_from_ms']),p['id'])):
        v=next(v for v in p['variants'] if v['language']==language and v['detail']=='simple' and v['focus']==focus)
        if p.get('family'):title=LABELS[p['family']][language=='es']
        else:title=(editorial_title if p['schema_version']=='4.0.0' else title_for)(p['narrative_plan'],p['metrics'],language) if p['schema_version'] in {'3.0.0','4.0.0'} else p['title']
        moments.append({'story_id':p['id'],'revision':p['revision'],'title':title,'text':v['text'],'family':p.get('family','pass'),'claim_ids':v['claim_ids'],
                        'at_ms':p['metrics'].get('occurrence_ms',p['eligible_from_ms']),'archived':cutoff>=p['expires_at_ms'],
                        'similar_moments':[{'story_id':p['id'],'revision':p['revision'],'at_ms':p['eligible_from_ms']}],
                        'selection_reason':'Confirmed goals first, then family round robin; latest possession window; chronological display.',
                        'evidence_path':f'/stories/{p["id"]}/evidence'})
    timeline_count=len({p.get('incident_id',p['id']) for p in relevant_packages})
    return {'selection_rule_version':'mixed-approved-v2','input_revisions':inputs,'projection_hash':digest(['mixed-approved-v2',inputs,language,focus]),
            'moments':moments,'approved_count':timeline_count,'distinct_count':len(incidents),'timeline_count':timeline_count,'truncated':timeline_count>len(moments)}
