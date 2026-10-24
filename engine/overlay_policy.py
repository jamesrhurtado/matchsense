"""Flagship-only stable overlay policy. Source withdrawal always wins."""
from engine.event_metrics import FAMILY_PRIORITY
HOLD_MS=8000


def choose_overlay(live, previous, now):
    if not live:return None
    ranked=sorted(live,key=lambda p:(FAMILY_PRIORITY.get(p.get('family','pass'),5),-p['metrics'].get('occurrence_ms',p['eligible_from_ms']),p['id']))
    best=ranked[0]
    if best.get('family')=='goal':return best
    if previous and 0<=now-previous['shown_at_ms']<HOLD_MS:
        held=next((p for p in live if all(p[k]==previous[k] for k in ('id','revision','package_hash'))),None)
        if held:return held
    return best
