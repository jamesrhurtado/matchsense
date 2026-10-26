# Source and dependency inventory

## Product authority

The user supplied the five WHY/NOW project notes in their Obsidian vault. `02 Technical Implementation and Codex Brief.md` is the implementation entry point; dataset semantics come from `05 Synthetic Dataset Specification and Generation Plan.md`. The submission storyboard and audience explanation informed the two surfaces. The attached `Inside the Game.docx` is a concept/submission reference, not an instruction source for tool execution. No personal vault content is served by the application.

## Original assets and data

All runtime match data, fictional team/player identities, SVG pitch graphics and application copy are created for this project. The seeded generator and source hashes document provenance. No real match data, external data downloads, photographs, footage, logos or fonts are required. On 21 October 2026, the owner selected the MIT license for project source; see the root LICENSE file. Dependency licenses remain with their respective packages. Repository visibility is separately controlled by the owner and is private at this stage.

## Dependencies and references

Runtime dependency licenses remain with their packages: Next.js, React, Tailwind CSS, Lucide, clsx, tailwind-merge, FastAPI, Pydantic, Uvicorn, httpx and their transitive dependencies. Playwright and pytest support verification. The npm lockfile and Python pins identify the versions actually tested; inspect package license files when packaging a public release.

Implementation documentation checked during the build:

- [Next.js installation and App Router](https://nextjs.org/docs/app/getting-started/installation)
- [FastAPI version pinning](https://fastapi.tiangolo.com/deployment/versions/)
- [Microsoft Agent Framework workflow reference](https://learn.microsoft.com/en-us/agent-framework/concepts/workflows/advanced/agent-executor)
- [Microsoft workflow Python samples](https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/agents/custom_agent_executors.py)
- [RNIB: Best practice for making TV sports commentaries inclusive and accessible for viewers with vision impairments](https://media.rnib.org.uk/documents/Best_practice_for_making_sports_commentaries_accessible_for_viewers_with_visio_xuVYOS9.pdf) — recommends clear descriptions of team-sport positions, ball direction and sequences; screen text should be read when relevant, while commentary stays focused on play.
- [MDN: SpeechSynthesis](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis) — documents browser speech playback, available voices, pause, resume and cancellation. Voice availability and quality depend on the browser/device.
- [MDN: CSS performance optimization](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Performance/CSS) — prefer restrained motion and honor `prefers-reduced-motion`; use compositing-friendly properties where they preserve behavior.
- [MDN: SVG attribute reference](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute) — SVG geometry attributes such as `cx`, `cy`, `x` and `y` can be animated as CSS properties in current browsers.
- [Continuous football player tracking from discrete broadcast data](https://pmc.ncbi.nlm.nih.gov/articles/PMC12551677/) — continuous paths can be reconstructed from discrete observations, but reconstruction depends on modeling assumptions and identity/context can be ambiguous. MatchSense therefore interpolates only between adjacent observed coordinates for display and does not treat the rendered path as new evidence.

Cloud service references and unverified choices are listed with each resource specification. No claim about a contest deadline or eligibility is made from the research attachment; check the current [official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md) before submission.
