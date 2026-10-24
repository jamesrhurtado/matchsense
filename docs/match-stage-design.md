# Match stage visual refresh

24 October 2026. Hackathon presentation work on the live pitch panel, shared by
producer and viewer. Evidence diagrams keep their existing presentation.

## Research and direction

References reviewed:

- [FotMob](https://www.fotmob.com/): a dedicated football match experience, with
  scores and contextual match information as the entry point.
- [Sofascore's redesign](https://www.sofascore.com/news/sofascores-new-home-screen-a-smarter-faster-way-to-follow-sports): simplify navigation and make the information fans follow easier to reach.
- [Flashscore match detail redesign](https://www.flashscore.com/news/new-look-match-details-on-flashscore-a-full-page-instead-of-a-small-window/QJg8Wtgg/): give match detail its own page and emphasize the match summary.
- [Premier League's digital platforms](https://www.premierleague.com/en/news/4337361/premier-league-launches-new-fan-facing-platforms-as-part-of-digital-transformation): verified match information alongside stories and player/club interests.

The design interpretation is an original broadcast-style match stage, rather
than a copy of any platform. Midnight blue chrome (#101e2b), ice blue (#92caff)
and amber (#f4c466) team identities, and grass green (#153f35–#2f7259).
The scoreboard leads; the pitch stays geometrically faithful; the approved
explanation becomes the lower third. Bold compact score typography and quieter
operational labels create hierarchy without adding another font dependency.

## Delivered behavior

- Prominent score, full team names, period and clock; original vector crests for
  the two fictional clubs. A missing source score displays dashes.
- Explicit synthetic-replay and replay-state labels, distinct source-confirmed
  score and producer-approved explanation labels.
- Textured grass, mowing stripes, pitch markings, shaded numbered markers and
  ball halo. These are visual treatments, not inferred metrics or movement.
- Current control label uses only the observed frame's possession team; missing
  control is explicitly labeled. No control percentages are invented.
- Segment progress uses actual replay elapsed/duration values, exposed accessibly.
- Editorial selection policy remains available through a keyboard-operable
  disclosure, removing long operational text from the main explanation.
- English/Spanish labels, responsive scoreboard and reduced-motion compatibility.
- No new external font, artwork, service, model call, deployment or package dependency.

## Verification

See [UI verification](../evals/match-coverage/ui-refresh/verification.md) for
desktop/mobile/Spanish screenshots and verification logs. Automated checks establish rendering and regression behavior;
no human preference or usefulness finding is claimed. Pilot participants are
still pending as documented in the implementation delivery record.

## Keeper and ball clarity follow-up

The mixed replay inherits general off-ball grid positions from
`simulator.suite.generate_case`; the metadata identifies keepers, but those
positions do not model goalkeeper movement. At 105 s this puts the home keeper
near the upper-left boundary and the away keeper near another player. These are
fixture limitations, not tactical behavior or inferred match events.

The live stage now reads explicit player `role` metadata to draw home/away
keepers with lavender/coral square kits and a bilingual legend. Shirt number
alone does not determine role. Missing role metadata does not invent a keeper.
Overlapping ball symbols use a neutral white football callout and a dashed
leader to the exact observed coordinate; all player coordinates stay unchanged.
The ball callout chooses a nearby corner with more space and stays within the
pitch. Evidence diagrams and existing replay files/packages are unchanged.
A future realism revision must be separately versioned rather than silently
rewriting source observations used by stored explanations.

## Controlled-ball badge follow-up

A later owner screenshot showed the linked ball's endpoint and dashed line still
covering a two-digit shirt number. In the live stage, a source-identified carrier
with a nearby observed ball now gets a small football badge beside the player,
without a center dot or leader line. The badge prefers a stable corner, avoids
nearby player markers when possible and uses more clearance for keeper squares.
The control outline is smaller. A bilingual note explains that it identifies the
observed carrier; it is a presentation badge, not the exact ball coordinate.
Source coordinates remain in the frame/evidence and are not changed.

Free/in-flight balls still use their observed coordinates, with an offset leader
only for overlapping markers. Those anchors now paint behind players so they
cannot obscure shirt numbers. A nearby player never becomes a carrier merely
because the ball is close; missing control/ball observations do not create a badge.
Evidence diagrams retain their existing exact-coordinate rendering.
