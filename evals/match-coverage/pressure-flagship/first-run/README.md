# First-run failures, retained for transparency

The first continuous run stopped on an unknown shot outcome. A copied display-text
branch in `evidence_state` referenced a language variable that did not exist in
that function. Removed it; the status is now the machine-readable
`awaiting_outcome`, while localized explanatory text belongs in `why_now`.
Added the focused unknown-outcome regression and reran continuous playback.
This same error interrupted cancellation/unknown-shot viewer updates.

The first full browser run also found the new relevance card pushing the original
mobile pass evidence below its established viewport expectation. Scoped the new
card to flagship sessions, preserving the old regression assertion.

The new browser test initially matched a hidden family-filter `<option>` rather
than the recap's visible heading. Corrected the test to query the heading role;
no product behavior or expectation was weakened.

These failed attempts are separate from the final verification results. No source
reference labels or original numerical regression expectations were changed.

The final focused test also needed the recap heading's level to distinguish it
from the explanation title, and `Idioma` when switching an already-Spanish page
back to English. Both were test locators; product translations were correct.
