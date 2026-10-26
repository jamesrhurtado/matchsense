"""Export one blinded, offline reviewer assignment from preserved discovery outputs.

No model calls, publication writes, or regenerated explanations. The reconstructed
runtime input must match every preserved result before any material is exported.
"""
from dataclasses import asdict
from pathlib import Path
import hashlib
import html
import json
import math
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evals.agentic.dataset import discovery_cases, fingerprint


def render_markdown(text):
    """Small static renderer for the controlled headings, prose and tables below."""
    def inline(s):
        s = html.escape(s)
        return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    result = []
    for block in text.strip().split('\n\n'):
        if block.startswith('|'):
            rows = block.splitlines()
            table = '<div class="table-scroll"><table><thead><tr>'
            table += ''.join('<th scope="col">'+inline(c.strip())+'</th>' for c in rows[0].strip('|').split('|'))
            table += '</tr></thead><tbody>'
            for row in rows[2:]:
                table += '<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in row.strip('|').split('|'))+'</tr>'
            result.append(table+'</tbody></table></div>')
        elif block.startswith('#'):
            level = len(block)-len(block.lstrip('#'))
            result.append(f'<h{level}>{inline(block[level:].strip())}</h{level}>')
        elif block.startswith('- '):
            result.append('<ul>'+''.join('<li>'+inline(line[2:])+'</li>' for line in block.splitlines())+'</ul>')
        else:
            result.append('<p>'+inline(block)+'</p>')
    return '\n'.join(result)


def main():
    run = ROOT/'.run/agentic-v4-live-comparison'
    case = next(c for c in discovery_cases() if c.case_id == 'relay-attribution')
    runtime = asdict(case.runtime)
    rows = [json.loads(line) for line in (run/'results.jsonl').read_text().splitlines()]
    selected = [r for r in rows if r['case_id'] == case.case_id]
    assert len(selected) == 4 and len({r['arm'] for r in selected}) == 4
    assert all(r['input_hash'] == fingerprint(runtime) for r in selected)
    packets = [p for p in json.loads((run/'rating-packets.json').read_text()) if p['case_id'] == case.case_id]
    assert len(packets) == 4
    mapping = json.loads((run/'rating-mapping-private.json').read_text())
    for p in packets:
        original = rows[mapping[p['rating_id']]['row_index']]['package']
        assert p['presentation']['title'] == original['title']
        assert p['presentation']['variants'] == original['variants']

    out = ROOT/'docs/reviewer-pack/assignments/F01'
    if out.exists():
        raise SystemExit('Refusing to overwrite an existing reviewer assignment.')
    out.mkdir(parents=True)
    meta, obs = runtime['metadata'], runtime['observations']
    people = {p['id']:p['name'] for p in meta['players']}
    team_names = {t['id']:t['name'] for t in meta['teams']}
    events = [m for m in obs if m['kind']=='event']
    start = next(m for m in events if m['payload']['type']=='pass_started')
    end = next(m for m in events if m['payload']['type']=='pass_resolved')
    frames = sorted([m for m in obs if m['kind']=='tracking_frame'],key=lambda m:m['timeline_ms'])
    frame = lambda t: next(m for m in frames if m['timeline_ms']==t)
    assert all(m['timeline_ms'] <= runtime['cutoff_ms'] and m['available_at_ms'] <= runtime['cutoff_ms'] for m in obs)
    passer = start['payload']['player_id']; receiver = end['payload']['details']['controlling_player_id']
    sx = start['payload']['details']['start_position']; ex = end['payload']['details']['end_position']
    release = frame(start['timeline_ms']); final = frame(runtime['cutoff_ms'])
    pre = [f for f in frames if start['timeline_ms']-2000 <= f['timeline_ms'] <= start['timeline_ms']]
    after = [f for f in frames if end['timeline_ms'] <= f['timeline_ms'] <= runtime['cutoff_ms']]
    assert len(pre)==21 and len(after)==31
    def proximity(f):
        ps=f['payload']['players']; a=next(p for p in ps if p['player_id']==passer)
        return sum(math.hypot(p['x_m']-a['x_m'],p['y_m']-a['y_m']) <= 6 for p in ps if p['team_id']!='blue')

    source = f'''# Source observations for assignment F01

Evidence set S01. Synthetic football passage; first-period coordinates in metres on a 105 by 68 m pitch. Harbor City attacks toward increasing x. The time shown is seconds from the start of this constructed replay. All supplied observations were available by 18.200 s. There is no real-match video for this scene.

This is a factual reading aid derived from the raw observation records, not a preferred explanation or a football usefulness score. Review the underlying records if you dispute the summary. Report uncertainty or inconsistencies. The same evidence applies to all four anonymous outputs.

## Events and positions

| Source ID | Time s | Observation |
|---|---|---|
| {start['message_id']} | 14.000 | {people[passer]} ({passer}, Harbor City) releases pass-1 from ({sx['x_m']}, {sx['y_m']}) m. |
| {end['message_id']} | 15.200 | Pass-1 is recorded as received by {people[receiver]} ({receiver}, Harbor City) at ({ex['x_m']}, {ex['y_m']}) m. |
| {final['message_id']} | 18.200 | Ball at ({final['payload']['ball']['x_m']}, {final['payload']['ball']['y_m']}) m. Possession team: {team_names[final['payload']['possession_team_id']]}. |

## Tracking through reception and afterward

The source contains 31 tracking frames from 15.200 to 18.200 s, at 0.100 s intervals. The following samples show the control transition. The complete frames are in source-observations.json; a controller is a player identity and possession team is a separate field.

| Source ID | Time s | Ball x m | Ball y m | Controlling player | Possession team |
|---|---|---|---|---|---|
'''
    for t in [15200,16000,16300,16400,17000,18200]:
        f=frame(t); p=f['payload']; source += f"| {f['message_id']} | {t/1000:.3f} | {p['ball']['x_m']} | {p['ball']['y_m']} | {people.get(p['controlling_player_id'],p['controlling_player_id'])} ({p['controlling_player_id']}) | {team_names[p['possession_team_id']]} |\n"
    source += f'''
Across those 31 frames, the recorded possession-team values are: {', '.join(team_names[t] for t in sorted({f['payload']['possession_team_id'] for f in after}))}. Check the player-control column separately when assessing player-specific wording.

## Opponents at the release frame

Frame {release['message_id']} at 14.000 s contains all 22 players. Below are the 11 opponent x positions. Compare them with the release and reception x coordinates above. These coordinates describe longitudinal placement, not defensive formations or intention.

| Player ID | Name | x m | y m |
|---|---|---|---|
'''
    for p in release['payload']['players']:
        if p['team_id']!='blue': source += f"| {p['player_id']} | {people[p['player_id']]} | {p['x_m']} | {p['y_m']} |\n"
    source += '''
## Opponent proximity before release

The following counts are calculated from each frame using straight-line distance from the passer, with a radius of 6 m. They describe proximity, not a calibrated probability or an assessment of intention. No frames in this window omit roster players.

| Source ID | Time s | Opponents within 6 m |
|---|---|---|
'''
    for f in pre: source += f"| {f['message_id']} | {f['timeline_ms']/1000:.3f} | {proximity(f)} |\n"
    source += '''
## Measurement definitions and scope

- Forward displacement is reception x minus release x for this attack direction. It is not the curved trajectory length of the ball.
- Post-reception forward displacement is ball x at 18.200 s minus reception x at 15.200 s.
- The pitch thirds are equal longitudinal bands: 0 to 35 m, 35 to 70 m, and 70 to 105 m. Describe boundary uncertainty if relevant.
- The current evidence window ends at 18.200 s. No shot, goal, later outcome, player intent, or match-wide conclusion is supplied.
- Synthetic positions are observations in a constructed case, not an expert-certified reconstruction of real football.

[Complete observation input](source-observations.json) includes metadata, roster identities, event records, all delivered tracking frames and the exact cutoff. It contains no output-generation method labels or reviewer answer key.
'''
    outputs = '# Anonymous explanations for assignment F01\n\nEvidence set S01 applies to every output. These are preserved outputs, not rewritten examples. Read and rate each ID independently, then compare. Identical wording is possible; ties are valid. Short and detailed text under one ID belong to the same output.\n\n'
    for p in packets:
        presentation=p['presentation']
        outputs += f"## Output {p['rating_id']}\n\n"
        if presentation is None:
            outputs += 'No explanation provided.\n\n'; continue
        outputs += 'Title: '+presentation['title']+'\n\n'
        for variant_id, heading in [('en_simple_general','Short explanation'),('en_detail_general','Detailed explanation')]:
            v=next(v for v in presentation['variants'] if v['id']==variant_id)
            outputs += f"### {heading}\n\n{v['text']}\n\n"

    ids=[p['rating_id'] for p in packets]
    assignment=f'''# Assigned football review session F01

Reviewer code F01. Evidence set S01. Allow 40 to 45 minutes. Review language: English. Prepared 22 October 2026.

This local page is your assigned offline content-review session. Open session.html in a browser; it needs no server, account or access token. It packages a frozen observation scene and its anonymous explanations. It does not connect to a live producer session or test application navigation.

## What to do

1. Read reviewer-manual.md or reviewer-manual.docx for your role and response scales.
2. Read the source summary below before opening the anonymous explanations. Use the complete observations if needed.
3. Review outputs in this order: {', '.join(ids)}. Complete one section of response-form.md per output; you can type into a copy in a text editor or use the Word manual's last page.
4. Rate each output independently, then record a preference or tie. Do not search for the generation methods or discuss answers before returning your response.
5. Return your completed response-form.md privately to the person who sent you this packet. Do not edit the original explanations or observations.

## Files provided

- [Source observation summary](source-summary.md)
- [Complete source observations](source-observations.json)
- [Anonymous explanations and output IDs](anonymous-explanations.md)
- [Assigned answer form](response-form.md)
- [Reviewer manual](reviewer-manual.docx)

This is one constructed discovery scene. It does not represent the whole product or a final accuracy benchmark. Some explanations may be identical; missing distinctions are a valid finding. There is no preferred answer. If material is missing or cannot be opened, record that problem rather than inventing a rating.

If you received only a local path from someone else's computer, ask them to send the complete ZIP folder. Localhost addresses and local paths are not publicly accessible across computers.
'''
    form='# Football review responses F01\n\nReviewer code: F01\n\nDate: ______\n\nRelevant football experience: ______\n\nPrior project exposure: ______\n\nEvidence set: S01\n\n'
    for rid in ids:
        form += f'''## Output {rid}

Your account of what happened and who did what: ______

Supporting source IDs and conclusions the evidence cannot establish: ______

Comparison scope if applicable, otherwise Not applicable: ______

Factual support 1 to 5 or Cannot judge: ______

Editorial usefulness 1 to 5 or Cannot judge: ______

Clarity 1 to 5 or Cannot judge: ______

Publish unchanged / Cosmetic edit / Substantive edit / Reject / Cannot judge: ______

Exact wording to change and your proposed correction: ______

Serious mistaken belief possible? Yes / No / Unsure. Explain: ______

If no output, was withholding appropriate? Yes / No / Cannot judge / Not applicable: ______

Missing material or technical difficulty: ______

'''
    form+='## Final comparison\n\nPreferred output ID, tie or no preference: ______\n\nWhy: ______\n\nMost important improvement: ______\n\nWould this help your football work? Why or why not? ______\n\nKeep original answers if you revise them after discussion. Do not fill unknown scores with zero. See reviewer-manual.md for scale anchors.\n'
    for filename,content in [('START-HERE.md',assignment),('source-summary.md',source),('anonymous-explanations.md',outputs),('response-form.md',form)]:
        (out/filename).write_text(content)
    (out/'source-observations.json').write_text(json.dumps(runtime,indent=2)+'\n')
    for ext in ['md','docx']:
        shutil.copyfile(ROOT/f'docs/reviewer-pack/01-football-reviewer.{ext}',out/f'reviewer-manual.{ext}')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>MatchSense review session F01</title><style>
body{font:17px/1.65 system-ui,sans-serif;color:#172b36;background:#f5f7f8;margin:0}main{max-width:960px;margin:auto;padding:32px 24px 80px;background:white}h1{font-size:30px;line-height:1.2}h2{font-size:23px;margin-top:36px}h3{font-size:18px}a{color:#07604b;text-underline-offset:3px}a:focus-visible,summary:focus-visible{outline:3px solid #1e6ca3;outline-offset:4px}nav{display:flex;gap:22px;flex-wrap:wrap;padding:16px 0;border-bottom:1px solid #ccd6dc}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #cbd5dc;text-align:left;padding:8px 10px}th{background:#eaf1ef}.table-scroll{overflow-x:auto}details{border-top:1px solid #ccd6dc;margin-top:32px;padding-top:18px}summary{cursor:pointer;font-size:22px;font-weight:650}section{scroll-margin-top:20px}footer{margin-top:40px;color:#526570}@media print{body{background:white}main{padding:0}details{display:block}nav{display:none}.table-scroll{overflow:visible}tr{break-inside:avoid}} </style><main><nav aria-label="Review sections"><a href="#assignment">Assignment</a><a href="#evidence">Source evidence</a><a href="#outputs">Anonymous outputs</a><a href="response-form.md" download>Download answer form</a></nav>'''
    page+='<section id="assignment">'+render_markdown(assignment)+'</section>'
    page+='<section id="evidence">'+render_markdown(source)+'</section>'
    page+='<details id="outputs"><summary>Open anonymous explanations after reviewing the evidence</summary>'+render_markdown(outputs)+'</details>'
    page+='<footer>Frozen offline review materials. No telemetry, model requests, stored browser answers or product mutations. Save your completed answer form separately.</footer></main></html>'
    (out/'session.html').write_text(page)
    private=ROOT/'.run/reviewer-assignments'; private.mkdir(exist_ok=True)
    manifest={'assignment':'F01','evidence_set':'S01','case_id':case.case_id,'purpose':'purposive first pilot for attribution and useful wording; not a sealed final',
        'input_hash':fingerprint(runtime),'input_matches_all_four_preserved_runs':True,'output_order':ids,
        'mapping':{rid:mapping[rid] for rid in ids},'run':'agentic-v4-live-comparison','prompt_version':'director-critic-v4.0',
        'scope':'original titles and English general short/detailed variants only; no output rewriting',
        'source_summary':'derived directly from runtime observations, not model claims; human validation pending',
        'file_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}}
    manifest_path=private/'F01-private-manifest.json'
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n'); manifest_path.chmod(0o600)
    archive=ROOT/'.run/F01-review-materials.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()): z.write(p,'F01/'+p.name)
    assert not any(token in page for token in ['"arm"','template_fallback','director-critic','rating-mapping-private','api_key'])
    print(json.dumps({'folder':str(out),'archive':str(archive),'output_ids':ids,'input_matches':True,'observation_count':len(obs),'files':len(list(out.iterdir()))}))


if __name__=='__main__':
    main()
