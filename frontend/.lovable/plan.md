
## Framework note

This Lovable project runs on **TanStack Start (React + TS + Vite)**, not Next.js. You confirmed it's fine to deliver the same app on this stack. All routes, contracts, components, validation, and error handling from FRONTEND_SPEC.md will be implemented verbatim. Only mechanical differences:

- File-routes use TanStack syntax (e.g. `farms.$farmId.tsx` ↔ `/farms/[farmId]`).
- Env var becomes `VITE_API_BASE_URL` (defaulting to `http://localhost:8000`) since Vite — not Next — handles env exposure. `NEXT_PUBLIC_API_BASE_URL` cannot be read by the browser here.
- Backend must enable CORS for the preview/published origin (browser calls the backend directly; no proxy).

## Routes

```
src/routes/
  __root.tsx             # AppShell: top nav (Dashboard / Farms / Usage)
  index.tsx              # Dashboard
  farms.tsx              # layout (<Outlet/>)
  farms.index.tsx        # /farms
  farms.new.tsx          # /farms/new
  farms.$farmId.tsx      # /farms/:farmId (detail)
  farms.$farmId.edit.tsx # /farms/:farmId/edit
  usage.tsx              # /usage
```

## API client (`src/lib/api/`)

- `client.ts`: `request<T>()` wrapper around `fetch` using `import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'`. Handles 204, JSON parse, throws `ApiError { status, detail, body }`. Multipart path doesn't set Content-Type.
- `types.ts`: all spec types (`Farm`, `FarmList`, `Advisory`, `OperationAdvisory`, `TreeAnalysis*`, `WeatherAiUsage`, `TreeQuota`, etc.).
- `endpoints.ts`: every function from spec §10 — `listFarms`, `getFarm`, `createFarm`, `updateFarm`, `deleteFarm`, `generateAdvisory`, `listAdvisories`, `getOperationAdvisory`, `uploadTreeAnalysis`, `getFarmTreeQuota`, `listTreeAnalyses`, `getWeatherAiUsage`, `getHealth`, `getReadiness`.

## Data layer

TanStack Query (already configured in router context) with `queryOptions` per resource and `defaultPreloadStaleTime: 0`. Mutations invalidate keys per spec §11 (farm CRUD → farms list; advisory gen → advisory history; tree upload → quota + tree history).

## Forms & validation (spec §4.2)

`react-hook-form` + `zod`:
- `farmer_name` 1–255, `county` 1–100, `crop_type` enum, `latitude` -90..90, `longitude` -180..180, `farm_size_acres` optional ≥ 0.
- Shared `FarmForm` used by new + edit.

## Error mapping (spec §11)

Central `apiErrorToMessage(err, ctx)` helper + toast/inline rendering:
- 404 → not-found view with link back to `/farms`
- 409 → "Duplicate farm" inline on FarmForm
- 413 → "Image exceeds size limit" on uploader
- 422 → field-level validation message or "Invalid operation"
- 429 → quota-exceeded banner; disable upload
- 502 → "WeatherAI upstream failed" with retry

## Components (spec §12)

`AppShell`, `MainNav`, `FarmList`, `FarmCard`, `FarmForm`, `FarmDeleteDialog`, `FarmSummary`, `AdvisoryPanel`, `AdvisoryDayCard`, `AdvisoryHistory`, `OperationAdvisor` (tabs for 5 ops + date picker), `RiskBadge` (color + text label for a11y), `QuotaCard`, `UsageOverview`, `TreeUploadPanel` (preview, 20MB client check, with_weather toggle, disabled when remaining≤0), `TreeAnalysisResult`, `TreeAnalysisHistory`, `EmptyState`, `ErrorState`, `LoadingState` (skeletons).

## Farm detail (spec §4.3)

Sections on `/farms/:farmId`: header (FarmSummary + edit/delete), QuotaCard, AdvisoryPanel (Generate/Refresh + cached badge + 7-day grid + recommendations), OperationAdvisor, TreeUploadPanel + TreeAnalysisResult, AdvisoryHistory (paginated), TreeAnalysisHistory (paginated). Quota and advisory lazy-loaded after farm record.

## Dashboard (spec §4.1)

Total farms, WeatherAI usage summary (link to /usage), recent 5 farms by `created_at` desc, quick actions (Add farm, View usage). Skeletons, empty state, retry on error.

## Usage page (spec §8)

Three QuotaCards (api/ai/trees) with progress bars; status badge (healthy/low/critical); 502 fallback message.

## Design

Operational, not marketing. Tailwind tokens via `src/styles.css` (extend semantic colors for risk: low=green, medium=amber, high=red — paired with text labels for a11y). Responsive: cards stack on mobile, tables get horizontal scroll, primary actions stay top on mobile.

## Tests

Vitest (already available) for:
- `client.ts`: URL composition, 204 handling, JSON success, JSON error → ApiError with status+detail, multipart no Content-Type.
- `farmSchema`: accepts valid, rejects out-of-bounds lat/long/size/crop.
- `RiskBadge`: renders all three bands with labels.
- `QuotaCard`: zero limit, low remaining.
- `TreeUploadPanel`: rejects >20MB locally; handles `weather: null` partial success.
- One smoke test for FarmForm submit.

## Deliverables checklist

1. App shell + nav + routes  
2. Typed API client + types + endpoints  
3. Farm CRUD (list, create, edit, delete with confirm dialog)  
4. Farm detail with advisory gen/history, operation advisor, tree upload/history, farm quota  
5. /usage page  
6. Zod validation matching backend  
7. 404/409/413/422/429/502 handling everywhere relevant  
8. Responsive desktop + mobile  
9. Vitest unit tests for client + critical components  
10. Build/lint pass

## Out of scope (per spec §15)

Auth, roles, map drawing, offline, push, direct WeatherAI calls, editing historical records.
