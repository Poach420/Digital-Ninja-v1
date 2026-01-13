# Deployment Console Walkthrough — 2026-01-10

## Feature Overview
- Multi-stage pipeline UI introduced in [frontend/src/components/DeploymentConsole.js](frontend/src/components/DeploymentConsole.js#L1-L210) with Provision → Promote badges, log stream, and platform selector.
- Project editor launches the console from the primary Deploy button per [frontend/src/pages/ProjectEditor.js](frontend/src/pages/ProjectEditor.js#L205-L233), preserving the editing context.
- Enhanced builder brings the same console into the header actions so autonomous projects can deploy without switching views via [frontend/src/pages/EnhancedBuilder.js](frontend/src/pages/EnhancedBuilder.js#L230-L310).

## Manual Smoke Checklist
1. Authenticate, open any existing project, and press **Deploy** to confirm the dialog renders, stage badges animate in sequence, and the log scrolls to the latest entry.
2. Repeat inside **Enhanced Builder** after loading a project to verify both surfaces share the unified pipeline overlay.

## Known Limitations
- Pipeline currently simulates stage durations while awaiting the backend response; real-time SSE streaming remains a future enhancement.
- Cancellation and retry controls are deferred to a later iteration once backend job management is available.
