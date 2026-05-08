# SmartTravel Data Platform

A no-code API management and travel data analytics platform for collecting, processing, and visualizing travel destination information.

## Run & Operate

- `pnpm --filter @workspace/smart-travel run dev` — run the frontend (port assigned by workflow)
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- Frontend: React + Vite (artifact: `artifacts/smart-travel/`)
- UI: Tailwind CSS v4, shadcn/ui components, Recharts
- Routing: wouter
- API client: axios with caching
- API: Express 5 (scaffold, `artifacts/api-server/`)
- DB: PostgreSQL + Drizzle ORM (scaffold)

## Where things live

- `artifacts/smart-travel/src/pages/` — all page components (one per route)
- `artifacts/smart-travel/src/components/` — shared UI components
- `artifacts/smart-travel/src/services/apiClient.js` — axios client, baseURL configurable via `VITE_API_URL`
- `artifacts/smart-travel/src/components/layout/app-sidebar.jsx` — navigation sidebar
- `artifacts/api-server/` — Express API server scaffold

## Architecture decisions

- Ported from Next.js (from Vercel) to Vite + React + wouter for Replit compatibility
- Next.js `useRouter` → wouter `useLocation` (navigate via `[, navigate] = useLocation()`)
- Next.js `useParams` → wouter `useParams`
- Next.js `Link` → wouter `Link`
- `next/dynamic` → React `lazy` + `Suspense`
- API baseURL defaults to `''` (empty) so pages calling `/api/*` routes hit the proxy correctly
- Original backend was Python FastAPI (`http://backend:8000`) — not ported; frontend shows graceful error states when API is unavailable

## Product

SmartTravel is a data platform dashboard with:
- Overview dashboard with system health metrics
- API Connections management (create, edit, delete, test)
- Pipeline scheduling and run history monitoring
- Travel analytics dashboards (Smart Travel Analytics)
- Data explorer and field mappings
- Admin portal for users, roles, and system settings
- Airflow pipeline lab integration

## Gotchas

- The original app connected to a Python FastAPI backend at `http://backend:8000` — this is not running in Replit, so all API calls will show error states. To wire up a real backend, either use the Express api-server scaffold or add a new Python service.
- `VITE_API_URL` env var can override the default API base URL if you set up a backend
