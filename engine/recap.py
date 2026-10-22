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
