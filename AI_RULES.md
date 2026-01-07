# AI Rules and Tech Choices

This document defines the approved tech stack and clear rules for which libraries to use and when, so contributions stay consistent and maintainable.

## Tech Stack Overview (5–10 bullets)
- Frontend: React 19 with Create React App (CRACO) and React Router for client-side routing.
- Styling: Tailwind CSS (dark mode via class) with shadcn/ui components built on Radix UI primitives.
- Forms & Validation: react-hook-form + zod for schema-based validation and type-safe constraints.
- HTTP & Data: axios for all API calls to the FastAPI backend.
- UI Utilities: clsx, tailwind-merge, and class-variance-authority for conditional classes and component variants.
- State: Local component state and React Context; no global state library by default.
- Interactions: @hello-pangea/dnd for drag-and-drop, react-resizable-panels for pane resizing.
- Rich UI: @monaco-editor/react for code editing, react-grid-layout for dashboards, embla-carousel-react for carousels.
- Dates: date-fns for formatting and utilities, react-day-picker for date inputs.
- Backend: FastAPI + Motor (MongoDB), Pydantic models, JWT auth (python-jose), password hashing (passlib).

## Frontend Rules

- Routing
  - Use react-router-dom for all navigation and route guards.
  - Keep route definitions centralized in frontend/src/App.js.

- Styling & Theming
  - Use Tailwind classes for all styling; do not introduce CSS-in-JS libraries.
  - Dark mode is class-based (tailwind.config.js uses darkMode: 'class').
  - Prefer CSS variables and Tailwind tokens; avoid inline styles except for dynamic values.

- UI Components
  - Prefer shadcn/ui components in frontend/src/components/ui for primitives (Button, Dialog, Tabs, etc.).
  - If a component needs customization, wrap shadcn/ui in a new component under frontend/src/components/ rather than modifying the ui/ files directly.
  - Use Radix primitives already installed when building accessible custom components.

- Icons & Feedback
  - Icons: lucide-react only.
  - Toasts/notifications: sonner. Render a single <Toaster /> at app root and use the sonner API throughout.
  - App-specific: import Toaster from frontend/src/components/ui/toaster.jsx and place it once near the root (e.g., in App.js or index.js). Use: import { toast } from 'sonner'.

- Forms & Validation
  - Forms: react-hook-form for form state and submission.
  - Validation: zod for schemas, with @hookform/resolvers/zod to integrate into react-hook-form.
  - Always validate user input at both the UI and API boundaries.

- Data Fetching
  - Use axios for all HTTP requests; do not mix in fetch for new code.
  - Centralize API helpers in frontend/src/utils/api.js. Reuse shared axios instances and interceptors.

- Dates & Time
  - Use date-fns for all date utilities (formatting, parsing, manipulation).
  - Use react-day-picker for interactive date inputs.

- Interactions & Layout
  - Drag and drop: prefer @hello-pangea/dnd (do not add other DnD libs). Avoid react-beautiful-dnd for new work.
  - Resizable panels: react-resizable-panels.
  - Grid layouts/dashboards: react-grid-layout.
  - Carousels: embla-carousel-react.
  - Code editors: @monaco-editor/react.

- State Management
  - Default to React local state and Context.
  - Do not add Redux/MobX/Zustand unless a cross-cutting performance or complexity need is demonstrated.

- File Structure
  - Pages live in frontend/src/pages/.
  - Reusable components live in frontend/src/components/.
  - Do not place new code inside frontend/src/components/ui; treat that directory as vendor components.

### Project-specific conventions and paths
- Routing is defined in frontend/src/App.js; keep it the single source of truth.
- HTTP client: define and reuse a single axios instance with interceptors in frontend/src/utils/api.js.
- Toasts: ensure a single Toaster is rendered (frontend/src/components/ui/toaster.jsx). Call notifications via sonner's toast API.
- CRACO: keep CRA overrides in frontend/craco.config.js; avoid ad-hoc build hacks elsewhere.

### Directory & naming conventions
- Directory names must be all lower-case (e.g., src/pages, src/components, src/components/ui).
- Create a new file for every new component or hook; keep components small and focused (target <100 lines).
- Do not colocate new app code inside frontend/src/components/ui; wrap those primitives instead.

## Backend Rules

- Framework & API
  - Use FastAPI for all HTTP endpoints. Keep routers modular and typed with Pydantic models.
  - CORS configuration must stay in backend/server.py using FastAPI's middleware.

- Database
  - Use MongoDB via Motor (AsyncIOMotorClient). Do not introduce ORMs.
  - All timestamps in UTC ISO format; convert to timezone-aware datetime on read.

- Auth
  - JWTs issued with python-jose; passwords hashed with passlib (bcrypt).
  - Never return password hashes; sanitize user documents at the API boundary.

- Config & Logging
  - Load env via python-dotenv; never hardcode secrets. Document required env in README.
  - Use the existing logging setup; prefer structured, concise logs.

- Services
  - Place reusable logic in backend/services/. Keep routes thin and delegate to services.
  - Follow the existing pattern in backend/services/email_service.py and backend/services/pdf_service.py for organization.

### Backend structure conventions
- Keep API entry in backend/server.py. Group endpoints with APIRouter. As features grow, move specific routes into dedicated modules and include them from server.py.
- Access Mongo via a shared AsyncIOMotorClient; avoid per-request client creation.
- Serialize datetimes to ISO strings when storing; parse to aware datetime when reading.

## Library Addition Policy

- Prefer existing, installed libraries listed above. Do not add new runtime dependencies without clear justification (size, accessibility, performance).
- If a new library is proposed, it must:
  - Replace or extend a limitation of the current stack.
  - Be actively maintained and light-weight.
  - Be approved and documented here before adoption.

## Performance & Accessibility

- Aim for lightweight, accessible components; leverage Radix primitives for a11y.
- Defer heavy modules (e.g., Monaco) when not visible; lazy-load routes when appropriate.
- Favor semantic HTML, proper labeling, and keyboard navigation support.

## Testing & Quality

- Keep components small and focused (<100 lines when possible).
- Co-locate small helpers with components or place shared utilities under frontend/src/lib or frontend/src/utils.
- Prefer pure functions and simple hooks; avoid overengineering.
- Use the existing ESLint setup; do not introduce additional linters without discussion.

## Do Not Use (for new code)

- window.fetch for API calls (use axios instead).
- CSS-in-JS libraries (e.g., styled-components, emotion).
- Alternative icon libraries (stick to lucide-react).
- Alternative DnD libraries (do not reintroduce react-beautiful-dnd).
- Alternative notification libraries (use sonner).