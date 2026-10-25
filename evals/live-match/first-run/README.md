# Diagnostic runs retained

The initial backend run exposed a force-template argument routing defect, followed
by three compatibility failures caused by freezing execution on legacy sessions.
Both were repaired and the complete 420-check run passed. Three additional new
feed checks passed separately.

The first browser live test used an obsolete evidence-button selector; it timed
out because the flagship button is “Check the evidence”. Its corrected template
and real-AI flows passed. Background lock scope and recomputation cadence were
also narrowed; browser timeout alone was not proof of lock starvation.

A broader browser run included obsolete duration labels and coincided with a
long host inactivity interval. The initial continuous single stream completed
without clock discontinuity, with all 25 references found; the two-stream phase
then jumped from about 104 seconds to the end in about one monotonic second.
Those two results are invalid sustained-operation evidence and remain retained.
The retry instruments clock discontinuities explicitly and repeats the two-stream
phase. No reference or expiry was relaxed to obtain a pass.
