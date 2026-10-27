"""Evaluation-only paired probes for a seeded, policy-weak Director proposal.

The forced historical angle is factually supported but conflicts with the
current provisional editorial policy. It is injected identically into S3/M3;
it never enters runtime observations or a production workflow.
"""
from copy import deepcopy
from dataclasses import replace

from engine.editorial_narrative import build_editorial_package
from engine.workflow import EvidenceTools
from .context_cases import context_cases


def fault_probe_cases():
    authored = {case.case_id: case for case in context_cases()}
    definitions = [
        ('seeded-marginal-gap', 'history-marginal', None,
         'Very small, supported historical gap.'),
        ('seeded-mid-gap', 'history-contrast', (15.0, 16.0, 17.0),
         'Supported gap below the current emphasis threshold.'),
        ('seeded-threshold-gap', 'history-threshold-adjacent', None,
         'Absolute threshold met; relative threshold narrowly missed.'),
    ]
    probes = []
    for probe_id, source_id, distances, description in definitions:
        source = authored[source_id]
        metadata = deepcopy(source.runtime.metadata)
        observations = deepcopy(source.runtime.observations)
        if distances is not None:
            by_pass = {f'h{i}': distance for i, distance in enumerate(distances)}
            for observation in observations:
                if observation.get('kind') != 'event':
                    continue
                payload = observation.get('payload', {})
                details = payload.get('details', {})
                pass_id = details.get('pass_id')
                if payload.get('type') == 'pass_resolved' and pass_id in by_pass:
                    details['end_position'] = {'x_m': 20 + by_pass[pass_id], 'y_m': 30}

        runtime = replace(source.runtime, metadata=metadata, observations=observations)
        tools = EvidenceTools(runtime.metadata, runtime.observations,
                              runtime.cutoff_ms, runtime.pass_id)
        baseline = build_editorial_package(tools)
        if baseline is None:
            raise ValueError(f'{probe_id}: expected an eligible current story')
        policy = baseline['metrics']['editorial_policy']
        if (baseline['metrics']['context']['relation'] != 'greater_than_each'
                or policy['comparison_recommended']):
            raise ValueError(f'{probe_id}: seeded historical emphasis must conflict with policy')

        seeded_plan = deepcopy(baseline['narrative_plan'])
        seeded_plan['angle'] = 'historical_contrast'
        # Validate that the injected proposal is structurally valid and uses
        # only observed claims; the challenge is weak emphasis, not false data.
        seeded = build_editorial_package(tools, plan=seeded_plan)
        if not seeded or seeded['narrative_plan']['angle'] != 'historical_contrast':
            raise ValueError(f'{probe_id}: seeded proposal did not survive contract validation')

        reference = deepcopy(source.reference)
        reference['seeded_fault'] = {
            'type': 'policy_weak_historical_emphasis',
            'initial_plan': seeded_plan,
            'initial_angle': 'historical_contrast',
            'policy_version': policy['version'],
            'policy_recommended': False,
            'expected_angle_constraint': 'not_historical_contrast',
            'policy_status': policy['status'],
        }
        probes.append(replace(source, case_id=probe_id,
                              description=description, runtime=runtime,
                              reference=reference))
    return probes
