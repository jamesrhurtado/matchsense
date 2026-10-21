"""Offline boundary audit for the planning handoff; never calls a model.

Run from the repository root with:
  .venv313/bin/python docs/next-iteration/evidence/audit_probe.py

Fake provider usage is intentionally synthetic and is NOT billable usage.
This records current behavior, not desired behavior or model failure frequency.
"""
from pathlib import Path
import json
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
helpers = runpy.run_path(str(ROOT / 'tests/test_foundry.py'))
make_tools = helpers['tools']
decision = helpers['decision']
editor = helpers['editor']
FakeProvider = helpers['FakeProvider']
run_workflow = helpers['run_foundry_workflow']

rows = []
for introduction in [
    'The pass split the defensive line and left the defence exposed.',
    'The pass failed and possession was lost.',
]:
    evidence = make_tools()
    draft = editor(evidence)
    draft['variants'][0]['text'] = introduction
    provider = FakeProvider([
        decision(), decision('supported'), draft, decision('supported')
    ])
    package = run_workflow(evidence, provider=provider)
    rows.append({
        'probe': 'permissive_fake_reviewer',
        'untrusted_introduction': introduction,
        'evidence_retained': evidence.compute_pass_metrics()['retained'],
        'package_returned': package is not None,
        'unsupported_introduction_survived': bool(package and any(
            v['text'].startswith(introduction) for v in package['variants'])),
        'fake_provider_calls': len(provider.calls),
        'published_to_viewers': False,
    })

provider = FakeProvider([decision('abstain')])
package = run_workflow(make_tools(), provider=provider)
rows.append({
    'probe': 'abstention_result_accounting',
    'package_returned': package is not None,
    'fake_provider_calls': len(provider.calls),
    'usage_available_in_return_value': bool(package and package.get('model_usage')),
    'note': 'Per-call telemetry can exist; package-based accounting has no outcome.',
})

proposal = 'They dominated the entire match.'
evidence = make_tools()
provider = FakeProvider([
    decision(), decision('revise', 'The team retained possession in this sequence.'),
    editor(evidence), decision('supported'),
])
run_workflow(evidence, proposed_text=proposal, provider=provider)
rows.append({
    'probe': 'context_separation',
    'producer_proposal_reaches_analyst': provider.calls[0][2].get('candidate_text_untrusted') == proposal,
    'producer_proposal_reaches_first_reviewer': provider.calls[1][2].get('candidate_text_untrusted') == proposal,
    'note': 'Separate role calls are not a blind or statistically independent fact check.',
})

print(json.dumps({
    'assessment_date_lima': '2026-10-21',
    'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'method': 'offline adversarial fake-provider boundary probes',
    'actual_model_calls': 0,
    'azure_changes': False,
    'findings': rows,
}, indent=2))
