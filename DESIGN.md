# Design

## Source of truth
Status: Active. Updated2026-11-06. User authorized actual sutura reader demo, Vercel deployment, repository and integration into the existing Bearblog article. Evidence: existing commerce-v1 catalog/CSV, product-probe HTTP results, writing-preferences.json.
## Brand
Plain technical editorial. White background, black ink, gray rules. No gradients, shadows, decorative artwork or product-performance claims. Trust comes from actual execution, raw SQL/results and explicit limitations.
## Product goals
Readers can inspect actual sutura output against clear controls, learn definition enforcement/provenance/anchors and see empty/refusal behavior. This is a fixed-question product demonstration, not live LLM chat or proof of improved AI accuracy.
## Personas and jobs
Developers reading the article. Choose a scenario, run it, inspect differing/matching outputs, SQL and data. Works embedded and as standalone page.
## Information architecture
One page. Intro/status → scenario selection → side-by-side live results → expandable SQL/definition evidence → source data / reproducibility links. Embed route removes unnecessary hero space.
## Design principles
Explain what is compared before showing numbers. Label intentionally incomplete controls and correct controls. Preserve refusal, missing rows and errors. Explain manual precomputed net/order flags. Only one primary Run comparison action.
## Visual language
System sans serif, monospace code. Main width1120px,24px desktop padding/16px mobile. Small square-corner panels with1px gray borders; generous line height. Black primary button; visible keyboard focus. No animation beyond subtle pending state.
## Components
Scenario buttons/select, primary run button, live status region, two result panels, semantic result tables, details blocks for SQL/provenance, source table tabs. Distinct empty/refusal/error text without relying on color.
## Accessibility
Native labels/buttons/select/details; aria-live polite for execution status; keyboard reachable controls; minimum44px targets. Tables have headers and captions, code scrolls within panel. Respect reduced motion.
## Responsive behavior
Two columns above760px; one below. No page horizontal overflow at375px. iframe uses responsivewidth and reasonablefixedheight plus standalone link. Full interface must remain usable if iframe is unsupported.
## Interaction states
Initial: clearly tell user to run selected scenario. Loading: disable Run only; show actual execution pending. Success: raw rows and derived display with units. Empty: showNo rows, never silently convert to0. Refusal: show actual code/detail. Network error: preserve prior result with explicit failure, no fake fallback.
## Content voice
English to match article. Plain descriptions. Every deliberate badSQL is labeled; no generated baseline called an observedAIerror. All outputs reflect actual engine execution; no newLLMcall.
## Implementation constraints
No third-party application dependencies. Pythonstdlib HTTP controller and SQLite controls; staticHTML/CSS/JS UI. Official sutura0.11.0 image pinned by digest. Do not copy secrets, account ledgers or workspace configuration into repository. Only syntheticdata. Tests cover protocol/selection/empty/refusal handling and actual container integrations.
## Open questions
Vercel login pending user action. Bearblog iframe acceptance must be tested against exactpublicpage. No other design question blocks implementation.
