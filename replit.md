# SmartTravel Data Platform

A no-code API management and travel data analytics platform for collecting, processing, and visualizing travel destination information.

## Run & Operate

- `pnpm --filter @workspace/smart-travel run dev` — run the frontend (port assigned by workflow)
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 8080, proxied at `/api`)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- Frontend: React + Vite (artifact: `artifacts/smart-travel/`)
- UI: Tailwind CSS v4, shadcn/ui components, Recharts
- Routing: wouter
- API client: axios (no caching), baseURL='' so `/api/*` hits Replit proxy
- API: Express 5 (`artifacts/api-server/`) — full in-memory mock covering all frontend endpoints
- DB: PostgreSQL + Drizzle ORM (scaffold, not yet used — API uses in-memory store)

## Where things live

- `artifacts/smart-travel/src/pages/` — all page components (one per route)
- `artifacts/smart-travel/src/components/` — shared UI components
- `artifacts/smart-travel/src/services/apiClient.js` — axios client, baseURL configurable via `VITE_API_URL`
- `artifacts/smart-travel/src/components/layout/app-sidebar.jsx` — navigation sidebar
- `artifacts/api-server/src/routes/data.ts` — all main API routes (~40 endpoints)
- `artifacts/api-server/src/routes/smarttravel.ts` — smart-travel analytics dashboard routes

## Architecture decisions

- Migrated from Next.js (Vercel) to Vite + React + wouter for Replit compatibility
- Next.js `useRouter` → wouter `useLocation` (navigate via `[, navigate] = useLocation()`)
- Next.js `useParams` → wouter `useParams`
- Next.js `Link` → wouter `Link`
- `next/dynamic` → React `lazy` + `Suspense`
- API baseURL defaults to `''` (empty) so frontend `/api/*` calls route through Replit proxy to port 8080
- Original backend was Python FastAPI (`http://backend:8000`) — replaced with Express in-memory mock
- Replit proxy: frontend on assigned port at `/`, API server on port 8080 at `/api`

## Product

SmartTravel is a data platform dashboard with:
- Overview dashboard with system health metrics
- API Connections management (create, edit, delete, test)
- Pipeline scheduling and run history monitoring
- Travel analytics dashboards (Smart Travel Analytics)
- Data explorer and field mappings
- Admin portal for users, roles, OSM config, enrichment config, and system settings
- Airflow pipeline lab integration (DAG management and run history)
- Analytics page with 30-day success rate and daily activity charts

## API endpoint coverage (artifacts/api-server)

All endpoints return data matching the frontend's exact field contracts:
- `GET/POST/PUT/DELETE /api/connections` + `/api/test-connection`
- `GET/DELETE/POST /api/runs` + logs/requests sub-routes + `/api/execute-run`
- `GET/POST/PUT/DELETE /api/schedules`
- `GET/PUT/DELETE /api/reports` + refresh
- `GET/POST/PUT/DELETE /api/users`, `/api/roles`
- `GET/POST/DELETE /api/keys/rapidapi`
- `GET/POST/DELETE /api/backups` + restore
- `GET/POST/DELETE /api/exports` + download + `/api/data/export`
- `GET /api/mappings`, `/api/parameter-modes`
- `GET/PUT /api/osm/config` — returns `{ cities: { key: { name, bbox } }, overpass_urls }`
- `GET/PUT /api/enrichment/config` — returns `{ fields, language, smart_delay, daily_limit }`
- `GET/PUT /api/system/settings`
- `GET /api/pipeline/status`, `/api/pipeline/runs`; `POST /api/pipeline/run`
- `GET /api/dashboard/pipeline-metrics`
- `GET /api/analytics` — summary, successRateHistory, dailyActivity, runsByConnection, statusDistribution
- `GET /api/analytics/success-rate-history`
- `GET /api/airflow/stats`, `/api/airflow/dags`, trigger/pause/resume, `/api/airflow/runs` (includes successTasks/failedTasks)
- `GET /api/status`, `/api/health`
- `GET /api/smart-travel/dashboard/*` — 10 sub-routes with Vietnam POI seed data

## Python FastAPI backend (backend/)

Running via Docker Compose (not active in Replit). Registered routers (backend/app/main.py):
- `system.router` at `/api` — status, settings, schedules CRUD, analytics, dashboard/pipeline-metrics, OSM/enrichment config, RapidAPI keys
- `airflow.router` at `/api/airflow` — stats, dags, trigger/pause/resume, runs (path-unified with frontend)
- `dashboard.router` at `/api/smart-travel/dashboard` — overview, top-places, places-by-category, etc.
- `places.router`, `pipeline.router`, `health.router` at `/api`
- `admin.router` at `/admin`

## MongoDB wiring (Express → MongoDB)

Express API server tries MongoDB first for key collections, falls back to in-memory:
- `artifacts/api-server/src/lib/mongo.ts` — MongoDB client (connects if MONGODB_URI env var set)
- Collections: `connections`, `runs`, `schedules` read from MongoDB when available
- Set `MONGODB_URI=mongodb+srv://...` env var to enable real data
