# Builder UI Audit — 2026-01-10

## Current Implementations
- [frontend/src/pages/Builder.js](frontend/src/pages/Builder.js) provides a single-column layout with a Build/Chat toggle, one prompt textarea, and a modal GenerationLogger overlay. It lacks multi-tab prompt surfaces, integration shortcuts, or recent project recall.
- [frontend/src/pages/ImprovedBuilder.js](frontend/src/pages/ImprovedBuilder.js) uses a richer progress log and preview iframe, but still offers a solitary prompt field, limited preset selection, and no reusable prompt templates.
- Recent projects live exclusively on [frontend/src/pages/Projects.js](frontend/src/pages/Projects.js); builder screens do not reveal historical context or allow reopening active sessions.
- Fast/Standard generation modes, app-type presets, and integration hint chips are not present in any builder variant.
- Chat mode operates independently from generated project context in Builder.js (separate state, no linkage to project IDs). ImprovedBuilder links chat to `currentProjectId`, but only after a generation completes and without UI to pick prior builds.

## Gap Summary vs Replit Target
1. **Dual Prompt Tabs** — No App/Design (or similar) tabbing to focus prompts; only a single textarea is exposed at a time.
2. **Integration Shortcuts** — No quick actions or slash commands to append integrations (stripe, auth, etc.).
3. **Fast Mode Toggle** — No switch for lightweight vs deep generation runs.
4. **App-Type Selector** — No curated templates or presets; manual text only.
5. **Recent Projects & Iteration** — Builder cannot resume or iterate on existing projects; navigation to `/editor/:id` is required.
6. **Persistent Chat Context** — Chat history resets per session and does not bind to project context until generation completes.
7. **Progress Pipeline Visualization** — GenerationLogger modal provides text logs but lacks stage badges or progress milestones mirroring Replit pipeline UI.

## Immediate Considerations
- Consolidate builder experience into a single enhanced page (likely Builder.js) with tabbed prompts, preset selectors, and context-aware chat.
- Reuse project list endpoint (`/projects`) to populate a "Recent Builds" sidebar with quick resume actions.
- Extend API layer to request historical project context when switching sessions.
- Update GenerationLogger to expose stage-based statuses aligning with Replit parity requirements.

## Post-Upgrade Snapshot (2026-01-10)
- Dual prompt surfaces implemented via tabs in [frontend/src/pages/Builder.js](frontend/src/pages/Builder.js#L574-L616), separating App and Design briefs with Ctrl+Enter generation shortcuts.
- Fast mode toggle, app-type selector, and reusable integration chips now live in [frontend/src/pages/Builder.js](frontend/src/pages/Builder.js#L545-L646), feeding structured metadata into the composite prompt payload.
- Contextual copilot sidebar introduces mode switching (Plan/Apply/General) and persistent per-project histories at [frontend/src/pages/Builder.js](frontend/src/pages/Builder.js#L687-L766).
- Recent project picker hydrates active context through [frontend/src/pages/Builder.js](frontend/src/pages/Builder.js#L189-L220) and highlights the selected build in the sidebar list at [frontend/src/pages/Builder.js](frontend/src/pages/Builder.js#L795-L824).
