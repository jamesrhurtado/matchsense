"""Human-readable projections from approved-package facts; no model reasoning."""

def why_now(package,language='en'):
    es=language=='es';m=package['metrics'];family=package.get('family','pass');f=m.get('facts',{})
    if family=='pressure':
        text=(f'La media de rivales cercanos bajó de {f["before"]["mean"]:.1f} a {f["after"]["mean"]:.1f} en un pase de {f["forward_m"]:.1f} m hacia delante.' if es else f'Average nearby opponents dropped from {f["before"]["mean"]:.1f} to {f["after"]["mean"]:.1f} around a {f["forward_m"]:.1f} m forward pass.')
        if f['stands_out']:text+=(' Además avanzó más que cada uno de los tres pases anteriores del equipo en esta repetición.' if es else ' It also travelled farther forward than each of the team’s previous three passes in this replay.')
        return text
    if family=='goal':
        before=f['score_before'];after=f['score']
        return (f"El gol confirmado cambió el marcador de {before['blue']}:{before['amber']} a {after['blue']}:{after['amber']} en ese momento." if es else f"The confirmed goal changed the score from {before['blue']}:{before['amber']} to {after['blue']}:{after['amber']} at that moment.")
    if family=='shot' and f['outcome']=='unknown':return 'La fuente registra un remate, pero su resultado sigue sin confirmar.' if es else 'The source records an attempt, but its outcome remains unconfirmed.'
    if family=='shot':return 'El remate ya tiene un resultado observado; no se estima la calidad de la ocasión.' if es else 'The attempt now has an observed outcome; this does not estimate chance quality.'
    if family=='recovery':return 'Existe una observación explícita de recuperación o cambio de control; no se deduce por cercanía.' if es else 'A source observation records a recovery or control change; it is not inferred from proximity.'
    if family=='possession':return 'Resume un intervalo concreto con su base de tiempo y cobertura; no representa todo el partido.' if es else 'This summarizes one declared interval with its time denominator and coverage, not the entire match.'
    c=m.get('context',{})
    if c.get('relation')=='greater_than_each':return 'Este pase avanzó más que cada uno de los tres pases completados anteriores del equipo en esta repetición.' if es else 'This pass travelled farther forward than each of the team’s previous three completed passes in this replay.'
    return 'El pase combina cercanía de rivales, avance observado y posesión posterior confirmada. No se afirma importancia táctica.' if es else 'This pass combines nearby opponents, observed progression and confirmed subsequent team possession. Tactical importance is not established.'


def evidence_state(package):
    m=package['metrics'];f=m.get('facts',{});family=package.get('family','pass')
    if family=='pressure':return 'complete' if min(f['before']['coverage'],f['after']['coverage'])==1 else 'limited'
    if family=='shot':return 'awaiting_outcome' if f['outcome']=='unknown' else 'limited' if f['location'] is None or not m['participants'].get('shooter') else 'complete'
    if family=='possession':return 'complete' if f['coverage']==1 and f['percentages'] is not None else 'limited'
    if family=='goal':return 'complete' if m['participants'].get('scorer') else 'limited'
    if family=='recovery':return 'complete' if m['participants'].get('recovering_player') else 'limited'
    return 'complete' if m.get('coverage',0)>=1 else 'limited'
