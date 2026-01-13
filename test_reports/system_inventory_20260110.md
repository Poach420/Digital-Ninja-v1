# System Inventory — 2026-01-10

## Backend Services
- ai_builder_service.py: primary async OpenAI-driven code generator with dependency injection and deployment file synthesis.
- ai_builder_service_v2.py: alternate builder variant with structured prompt chaining (needs parity review).
- builder_server.py: FastAPI entry point exposing project generation, project retrieval, deployment, and analytics routes.
- server.py: legacy FastAPI server wrapper kept for compatibility; references builder_server under old import path.
- analytics_service.py: aggregates usage metrics and builder performance data.
- deployment_service.py: baseline deployment orchestration (pre-enhanced pipeline).
- deployment_service_enhanced.py: multi-platform (Vercel/Render/Railway) deployment with structured status responses.
- one_click_deploy.py: CLI orchestrator invoking deployment services.
- file_storage_service.py: handles persistent storage of generated artifacts and assets.
- discussion_service.py: manages team discussion threads tied to projects.
- database_auto_setup.py: prepares MongoDB collections and indexes.
- version_control_service.py: wraps git operations for generated projects.
- view_project.py: prepares packaged project snapshot payloads.
- services/email_service.py: transactional email delivery helper.
- services/pdf_service.py: PDF export utilities.
- auxiliary scripts: check_generated.py, check_recent_projects.py, autonomous_agent.py provide validation and automation helpers.

## Backend Tests
- test_ai_direct.py, test_new_generation.py: integration tests validating AI builder prompts and outputs.
- test_features.py: verifies generation of multi-component project outputs.
- test_services.py: covers builder service API-level behaviours.
- test_v2_builder.py: regression coverage for ai_builder_service_v2 pipeline.
- tests/unit/test_deployment_service_enhanced.py: unit coverage for enhanced deployment orchestration.

## Frontend Pages & Shell
- src/App.js with routing loader; App.css and global styles in index.css.
- src/pages/Builder.js, ImprovedBuilder.js, EnhancedBuilder.js, AiBuilder.js: assorted builder UIs (current parity focus areas).
- src/pages/PageBuilder.js and ProjectEditor.js: advanced editing surfaces.
- src/pages/Dashboard.js, Projects.js, AdminDashboard.js: project management workflows.
- src/pages/Login.js, Register.js, AuthCallback.js: authentication flow.
- src/pages/Settings.js, Billing.js, TeamManagement.js, Diagnostics.js: account, billing, team, and health tooling.
- src/components/: shared UI elements (menus, layout, inputs).
- src/hooks/, src/utils/, src/lib/: state, API clients, helper utilities.

## Deployment & DevOps Assets
- backend/Dockerfile and frontend/Dockerfile: container definitions for respective services.
- docker-compose.yml: orchestrates combined backend/frontend stack locally.
- render.yaml and vercel.json: hosted deployment manifests.
- DEPLOYMENT.md and DEPLOYMENT_INFRASTRUCTURE.md: documented deployment procedures.
- backend/one_click_deploy.py plus deployment_service_enhanced.py: runtime deployment automation.
- backend/PROOF_TEST.py and PROOF_GENERATION_OUTPUT.json: generation proof harness placeholders.

## Additional Infrastructure & Docs
- backend/requirements.txt, frontend/package.json: dependency manifests (backend pinned to virtualenv).
- test_reports/: historical regression outputs; new artifact appended here.
- important history/: continuity, automation, and parity directives guiding further upgrades.
