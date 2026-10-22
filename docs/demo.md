# Demonstrating WHY/NOW

For the current v0.5 candidate, use the [presenter script and rehearsal run sheet](demo-script-v4.md): a four-minute product walkthrough, two-minute cut, exact contextual replay setup, and narration for actual AI or local template mode. The hosted instructions below describe the earlier engineering build.

## Hosted rehearsal

Open the public application with the private producer key described in [QA guide](qa.md). The catalogue contains the original three replays plus 168 expanded synthetic segments. Choose **Synthetic segment 028 · 3 min** (`match-ce88c61d5a0c5d1d`) for the multi-moment demo. It has passes at 12 s, 72 s and 132 s; confirmations occur at 16.2 s, 76.2 s and 136.2 s. The actor names are Beni Prado (passer) and Jori Luna (receiver).

1. Show the synthetic pitch, fictional teams and producer console. At 1×, play until 20 s and pause. For a shorter rehearsal, use **Jump to second → 20 → Jump forward**. State that this is replay navigation; the clock pauses at the requested point.
2. Wait for the actual AI review package. Open **Show why**, replay the evidence and show the three longitudinally bypassed opponents and seven metres of post-reception progression. Explain the proximity/geometry limitations rather than claiming tactical intent or a scientifically established line break.
3. Open **Processing & review trace**. Show the actual execution mode and analyst/reviewer/editor actions, including a real request or revision if one occurred. Token counts are measured. If mode says template fallback, describe it honestly and rehearse again before presenting an AI execution claim.
4. Approve Moment 1. Open the viewer companion; show the shared overlay and a detailed Spanish explanation focused on the actual receiver, Jori Luna. Viewer changes select stored approved variants rather than running a model per viewer.
5. In the producer console, jump forward to 80 s and wait for Moment 2's review. Moment 1 remains an approved archive entry; approving Moment 2 does not overwrite it. The current overlay follows the newer live approved moment, regardless of which archive entry is selected.
6. In the companion, choose **Catch me up**. The recap contains both approved moments. Selecting Moment 1 reopens its evidence while Moment 2's shared overlay remains unchanged.
7. If time permits, select the archived Moment 1 in the producer queue and retract it. Only that moment disappears from viewer history and recap. Otherwise reserve retraction and the third pass (jump to 140 s) for engineering QA.

Each original overlay ends 30 s after its own confirmation, at 46.2 s, 106.2 s and 166.2 s in this replay. Pausing gives the producer time to inspect actual AI output; wall-clock model latency does not advance a paused replay. Expiry ends the live overlay, while an approved archive remains inspectable and retractable.

## Approximately 115-second recording

| Video time | Show and explain |
|---|---|
| 0–10 s | Broadcaster problem: explain why a pass mattered with inspectable support |
| 10–30 s | Working synthetic replay and evidence inspection; visibly pause or disclose a replay jump |
| 30–50 s | Actual agent review trace and exact-revision producer approval |
| 50–70 s | Viewer overlay, simple/detail modes and Spanish player focus |
| 70–100 s | Second independently reviewed moment, queue history and two-moment recap |
| 100–115 s | Brief Azure pipeline and measured engineering evidence: 168 constructed scenarios, 594 checkpoints; no real-match accuracy claim |

Rehearse actual workflow latency before recording. Use the stable original segment 1 if a simpler single-moment narrative better fits the time limit; its confirmation is 22.2 s and expiry 52.2 s, with Theo Vega as passer. Never stage an unsupported producer edit as a spontaneous AI mistake. A final video has not yet been recorded or published.

## Local mode and limits

The same interface runs locally with deterministic templates and SQLite. Say **local template mode**; there are no actual model calls in that mode. The full offline regression remains an engineering test on six authored parents, not an independently blind football benchmark. See [expanded results](../evals/synthetic-v2/REPORT.md) and [QA record](qa.md).

No shot, goal, full-time result, real footage, professional broadcaster integration or external television synchronization is implemented. Model review is fallible, and a comparative advantage over a fairly configured single agent has not been measured.
