# Replit Parity Gap Analysis (2026-01-10)

## Builder Experience
- Builder workspace now offers App/Design prompt tabs, fast-mode toggle, integration chips, and project-type presets in [frontend/src/pages/Builder.js](frontend/src/pages/Builder.js#L545-L646), aligning with the Replit dual-surface flow.
- Recent project resume cards and per-project chat state are integrated into the right rail via [frontend/src/pages/Builder.js](frontend/src/pages/Builder.js#L687-L824), enabling iterative prompting without leaving the page.
- Generation logger still lacks the multi-stage pipeline treatment (Provision/Security/Build/Bundle/Promote) and badge-based progress telemetry expected from Replit's console.

## Deployment Console
- Multi-stage pipeline console now renders Provision → Promote stages with logs via [frontend/src/components/DeploymentConsole.js](frontend/src/components/DeploymentConsole.js#L1-L210), mirroring Replit's deployment visualisation.
- Editor launches the console from the deploy button so builders see the same timeline without leaving the IDE per [frontend/src/pages/ProjectEditor.js](frontend/src/pages/ProjectEditor.js#L205-L233).
- Enhanced builder header exposes the same console for existing projects, keeping parity across flows per [frontend/src/pages/EnhancedBuilder.js](frontend/src/pages/EnhancedBuilder.js#L230-L310).
- Remaining gaps: no cancel/retry yet, no backend event streaming, and success states still rely on the synchronous response rather than live SSE telemetry.

## Account & Settings Suite
- Settings screen only covers profile fields, password placeholders, and generic notification toggles without backend persistence beyond toasts per [frontend/src/pages/Settings.js](frontend/src/pages/Settings.js#L10-L109).
- No dedicated pages for account, referrals, roles, secrets, connected services, domains, or theme management; routes list confirms absence across [frontend/src/pages](frontend/src/pages).
- Billing view lists plans and payment placeholder but lacks deeper management for invoices, usage history, or roles/seat controls expected in Replit parity.

## Documentation Hub
- Workspace lacks any documentation portal or navigation shell; there is no page/component dedicated to docs browsing under [frontend/src/pages](frontend/src/pages).
- Existing knowledge base markdowns (e.g., AI_RULES.md, EXPORT_GUIDE.md) are not surfaced in the app.

## Credits & Upgrade Visibility
- Dashboard only displays aggregate counts and plan label per [frontend/src/pages/Dashboard.js](frontend/src/pages/Dashboard.js#L42-L160); there is no credit balance, consumption graph, or upgrade CTA integrating with proof-of-usage requirements.
- Builder/deployment flows do not mention credit consumption or gating state.

## Test Evidence (Audit)
- Full backend pytest run logged in [test_reports/backend_pytest_20260110.log](test_reports/backend_pytest_20260110.log) fails during collection due to missing `token` fixture, lack of async plugin wiring, and reliance on live services (MongoDB, running API server).
- Targeted unit coverage in [test_reports/backend_unit_pytest_20260110.log](test_reports/backend_unit_pytest_20260110.log) passes for deployment_service_enhanced, confirming core token guards/config builders.
- Attempted rerun documented in [test_reports/backend_pytest_blockers_20260110.log](test_reports/backend_pytest_blockers_20260110.log) shows the suite hanging when environment credentials are absent; mocks or fixtures are required before CI can execute end-to-end.
- Frontend test command (`pnpm --filter frontend test -- --watch=false`) exits with code 1 and reports zero test files, revealing the absence of Jest coverage; see [test_reports/frontend_craco_test_20260110.log](test_reports/frontend_craco_test_20260110.log).

## Next Focus
- Introduce comprehensive fixtures/plugins so async backend tests execute and cover builder/deployment flows.
- Draft implementation plan for Replit-grade builder UI (dual tabs, fast mode, integrations, recent projects) and deployment pipeline with log streaming.
- Design account suite expansions (roles, secrets, services, domains, themes), in-app documentation browser, and credit telemetry before proceeding to build phase.
