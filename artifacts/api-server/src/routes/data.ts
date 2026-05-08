import { Router } from "express";

const router = Router();

const startTime = Date.now();

const connections = [
  { id: "conn-1", name: "MongoDB Atlas", type: "database", status: "connected", host: "cluster0.mongodb.net", port: 27017, database: "smarttravel", username: "admin", lastUsed: new Date().toISOString(), createdAt: new Date(Date.now() - 86400000 * 10).toISOString() },
  { id: "conn-2", name: "OpenStreetMap Overpass API", type: "api", status: "connected", host: "overpass-api.de", port: 443, database: "", username: "", lastUsed: new Date().toISOString(), createdAt: new Date(Date.now() - 86400000 * 8).toISOString() },
  { id: "conn-3", name: "Google Places API", type: "api", status: "connected", host: "maps.googleapis.com", port: 443, database: "", username: "", lastUsed: new Date().toISOString(), createdAt: new Date(Date.now() - 86400000 * 7).toISOString() },
  { id: "conn-4", name: "PostgreSQL Analytics", type: "database", status: "disconnected", host: "localhost", port: 5432, database: "analytics", username: "postgres", lastUsed: new Date(Date.now() - 86400000 * 2).toISOString(), createdAt: new Date(Date.now() - 86400000 * 5).toISOString() },
  { id: "conn-5", name: "Redis Cache", type: "cache", status: "connected", host: "localhost", port: 6379, database: "", username: "", lastUsed: new Date().toISOString(), createdAt: new Date(Date.now() - 86400000 * 3).toISOString() },
];

const runs = [
  { id: "run-1", connectionId: "conn-1", connectionName: "MongoDB Atlas", status: "completed", startTime: new Date(Date.now() - 3600000).toISOString(), endTime: new Date(Date.now() - 3300000).toISOString(), recordsExtracted: 15420, logSummary: "Successfully processed 15420 records for hanoi", city: "hanoi", type: "restaurant" },
  { id: "run-2", connectionId: "conn-2", connectionName: "OpenStreetMap Overpass API", status: "completed", startTime: new Date(Date.now() - 7200000).toISOString(), endTime: new Date(Date.now() - 6800000).toISOString(), recordsExtracted: 8930, logSummary: "Extracted 8930 POIs from OSM for hcmc", city: "hcmc", type: "attraction" },
  { id: "run-3", connectionId: "conn-3", connectionName: "Google Places API", status: "failed", startTime: new Date(Date.now() - 10800000).toISOString(), endTime: new Date(Date.now() - 10600000).toISOString(), recordsExtracted: 0, logSummary: "API rate limit exceeded", city: "danang", type: "hotel" },
  { id: "run-4", connectionId: "conn-1", connectionName: "MongoDB Atlas", status: "completed", startTime: new Date(Date.now() - 86400000).toISOString(), endTime: new Date(Date.now() - 86000000).toISOString(), recordsExtracted: 22100, logSummary: "Full sync completed for hue", city: "hue", type: "restaurant" },
  { id: "run-5", connectionId: "conn-2", connectionName: "OpenStreetMap Overpass API", status: "running", startTime: new Date(Date.now() - 1800000).toISOString(), endTime: null, recordsExtracted: 4210, logSummary: "In progress: collecting data for quangnam", city: "quangnam", type: "attraction" },
];

const schedules = [
  { id: "sched-1", connectionId: "conn-1", connectionName: "MongoDB Atlas", name: "Daily Hanoi Sync", status: "active", frequency: "daily", cronExpression: "0 2 * * *", nextRun: new Date(Date.now() + 3600000 * 6).toISOString(), lastRun: new Date(Date.now() - 3600000).toISOString(), enabled: true },
  { id: "sched-2", connectionId: "conn-2", connectionName: "OSM Overpass API", name: "Weekly OSM Full Scan", status: "active", frequency: "weekly", cronExpression: "0 1 * * 0", nextRun: new Date(Date.now() + 86400000 * 5).toISOString(), lastRun: new Date(Date.now() - 86400000 * 2).toISOString(), enabled: true },
  { id: "sched-3", connectionId: "conn-3", connectionName: "Google Places API", name: "Google Enrichment", status: "paused", frequency: "daily", cronExpression: "0 4 * * *", nextRun: null, lastRun: new Date(Date.now() - 86400000 * 3).toISOString(), enabled: false },
  { id: "sched-4", connectionId: "conn-4", connectionName: "PostgreSQL Analytics", name: "Analytics Rollup", status: "active", frequency: "hourly", cronExpression: "0 * * * *", nextRun: new Date(Date.now() + 3600000).toISOString(), lastRun: new Date(Date.now() - 3600000).toISOString(), enabled: true },
  { id: "sched-5", connectionId: "conn-5", connectionName: "Redis Cache", name: "Cache Warmup", status: "active", frequency: "daily", cronExpression: "30 0 * * *", nextRun: new Date(Date.now() + 3600000 * 18).toISOString(), lastRun: new Date(Date.now() - 3600000 * 6).toISOString(), enabled: true },
];

const reports = [
  { id: "rpt-1", name: "Monthly Travel Summary", description: "Monthly analytics report for all cities", type: "analytics", status: "ready", lastRefreshed: new Date(Date.now() - 3600000 * 2).toISOString(), createdAt: new Date(Date.now() - 86400000 * 30).toISOString(), data: { totalPlaces: 48231, avgRating: 4.2, topCity: "Hanoi" } },
  { id: "rpt-2", name: "API Key Health Report", description: "Status and usage of all RapidAPI keys", type: "system", status: "ready", lastRefreshed: new Date(Date.now() - 3600000).toISOString(), createdAt: new Date(Date.now() - 86400000 * 15).toISOString(), data: { totalKeys: 5, activeKeys: 4, blockedKeys: 1 } },
  { id: "rpt-3", name: "Pipeline Performance", description: "Pipeline execution metrics and trends", type: "performance", status: "generating", lastRefreshed: null, createdAt: new Date(Date.now() - 86400000 * 7).toISOString(), data: null },
];

const users = [
  { id: "usr-1", email: "admin@smarttravel.io", name: "Admin User", role: "admin", status: "active", lastLogin: new Date(Date.now() - 3600000).toISOString(), createdAt: new Date(Date.now() - 86400000 * 60).toISOString() },
  { id: "usr-2", email: "analyst@smarttravel.io", name: "Data Analyst", role: "analyst", status: "active", lastLogin: new Date(Date.now() - 86400000).toISOString(), createdAt: new Date(Date.now() - 86400000 * 30).toISOString() },
  { id: "usr-3", email: "viewer@smarttravel.io", name: "Report Viewer", role: "viewer", status: "inactive", lastLogin: new Date(Date.now() - 86400000 * 14).toISOString(), createdAt: new Date(Date.now() - 86400000 * 20).toISOString() },
];

const roles = [
  { id: "role-1", name: "Administrator", description: "Full access to all system features and management", permissions: ["all", "manage_users", "manage_keys", "system_config"] },
  { id: "role-2", name: "Analyst", description: "Read and write access to data and reports", permissions: ["read_data", "write_reports", "run_pipelines"] },
  { id: "role-3", name: "Viewer", description: "Read-only access to dashboards and reports", permissions: ["read_data", "read_reports"] },
];

let apiKeys = [
  { id: 1, key: "abc12345defgh", short_key: "abc12345...h", label: "RAPID_API_KEY1", status: "Ready", status_code: 200, createdAt: new Date(Date.now() - 86400000 * 30).toISOString() },
  { id: 2, key: "xyz98765abcde", short_key: "xyz98765...e", label: "RAPID_API_KEY2", status: "Ready", status_code: 200, createdAt: new Date(Date.now() - 86400000 * 20).toISOString() },
  { id: 3, key: "lmn54321qrstu", short_key: "lmn54321...u", label: "RAPID_API_KEY3", status: "Rate Limited (429)", status_code: 429, createdAt: new Date(Date.now() - 86400000 * 10).toISOString() },
];

const backups = [
  { id: "bkp-1", name: "auto_backup_20260501_020000.sql", size: 52428800, createdAt: new Date(Date.now() - 86400000 * 7).toISOString(), status: "completed" },
  { id: "bkp-2", name: "auto_backup_20260508_020000.sql", size: 55834624, createdAt: new Date(Date.now() - 86400000).toISOString(), status: "completed" },
];

const exports_ = [
  { id: "exp-1", name: "hanoi_pois_export.json", format: "json", status: "ready", size: 12345678, createdAt: new Date(Date.now() - 3600000 * 5).toISOString(), connectionId: "conn-1" },
  { id: "exp-2", name: "hcmc_restaurants.csv", format: "csv", status: "ready", size: 4567890, createdAt: new Date(Date.now() - 3600000 * 2).toISOString(), connectionId: "conn-2" },
  { id: "exp-3", name: "full_dataset_export.json", format: "json", status: "processing", size: 0, createdAt: new Date(Date.now() - 1800000).toISOString(), connectionId: "conn-1" },
];

const mappings = [
  { id: "map-1", name: "OSM to MongoDB", sourceField: "name", targetField: "name", type: "direct", connectionId: "conn-2" },
  { id: "map-2", name: "OSM to MongoDB", sourceField: "lat", targetField: "location.lat", type: "direct", connectionId: "conn-2" },
  { id: "map-3", name: "Google to MongoDB", sourceField: "rating", targetField: "rating", type: "direct", connectionId: "conn-3" },
  { id: "map-4", name: "Google to MongoDB", sourceField: "user_ratings_total", targetField: "reviewCount", type: "direct", connectionId: "conn-3" },
];

const parameterModes = [
  { id: "pm-1", name: "Full Sync", description: "Collect all data from scratch", parameters: { limit: 10000, offset: 0, enrichment: true }, connectionId: "conn-2" },
  { id: "pm-2", name: "Incremental", description: "Only new or updated records", parameters: { limit: 1000, since: "last_run", enrichment: true }, connectionId: "conn-2" },
  { id: "pm-3", name: "Test Run", description: "Small batch for testing", parameters: { limit: 10, offset: 0, enrichment: false }, connectionId: "conn-2" },
];

let osmConfig = {
  cities: { hanoi: ["restaurant", "attraction"], hcmc: ["restaurant", "hotel"], danang: ["attraction", "beach"] },
  overpass_urls: ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
};

let enrichmentConfig = {
  enabled: true,
  provider: "google_places",
  batch_size: 50,
  rate_limit_delay_ms: 200,
  fields: ["rating", "user_ratings_total", "photos", "opening_hours"]
};

const airflowDags = [
  { dagId: "smarttravel_osm_pipeline", description: "Main OSM data collection pipeline", isPaused: false, isActive: true, lastRun: new Date(Date.now() - 3600000).toISOString(), nextRun: new Date(Date.now() + 3600000 * 23).toISOString(), successRate: 98.2 },
  { dagId: "smarttravel_enrichment", description: "Google Places enrichment pipeline", isPaused: false, isActive: true, lastRun: new Date(Date.now() - 7200000).toISOString(), nextRun: new Date(Date.now() + 3600000 * 22).toISOString(), successRate: 96.5 },
  { dagId: "smarttravel_backup", description: "Automated database backup", isPaused: false, isActive: true, lastRun: new Date(Date.now() - 86400000).toISOString(), nextRun: new Date(Date.now() + 3600000 * 20).toISOString(), successRate: 100.0 },
  { dagId: "smarttravel_analytics_rollup", description: "Analytics aggregation and rollup", isPaused: true, isActive: false, lastRun: new Date(Date.now() - 86400000 * 2).toISOString(), nextRun: null, successRate: 91.3 },
];

function getUptimeString(): string {
  const ms = Date.now() - startTime;
  const hours = Math.floor(ms / 3600000);
  const days = Math.floor(hours / 24);
  const remHours = hours % 24;
  return days > 0 ? `${days} days, ${remHours} hours` : `${hours} hours`;
}

function makeId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

// --- STATUS & HEALTH ---
router.get("/status", (_req, res) => {
  const totalRuns = runs.length;
  const completedRuns = runs.filter(r => r.status === "completed").length;
  const successRate = totalRuns > 0 ? Math.round((completedRuns / totalRuns) * 100 * 10) / 10 : 0;
  res.json({
    status: "healthy",
    health: "healthy",
    uptime: getUptimeString(),
    activeUsers: users.filter(u => u.status === "active").length,
    totalConnections: connections.length,
    connections: { active: connections.filter(c => c.status === "connected").length, total: connections.length },
    schedules: { total: schedules.length, active: schedules.filter(s => s.status === "active").length },
    runs: { total: totalRuns, last24h: runs.filter(r => new Date(r.startTime) > new Date(Date.now() - 86400000)).length },
    activity: { successRate, totalRuns },
    performance: { successRate, avgResponseTime: 245 }
  });
});

router.get("/system/status", (_req, res) => {
  res.redirect("/api/status");
});

router.get("/health", (_req, res) => {
  res.json({ status: "alive" });
});

router.get("/monitoring", (_req, res) => {
  res.redirect("/api/status");
});

// --- CONNECTIONS ---
router.get("/connections", (_req, res) => {
  res.json(connections);
});

router.post("/connections", (req, res) => {
  const conn = { id: makeId("conn"), createdAt: new Date().toISOString(), lastUsed: new Date().toISOString(), status: "disconnected", ...req.body };
  connections.push(conn as typeof connections[0]);
  res.status(201).json(conn);
});

router.get("/connections/:id", (req, res) => {
  const conn = connections.find(c => c.id === req.params.id);
  if (!conn) return res.status(404).json({ error: "Connection not found" });
  res.json(conn);
});

router.put("/connections/:id", (req, res) => {
  const idx = connections.findIndex(c => c.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Connection not found" });
  connections[idx] = { ...connections[idx], ...req.body, id: req.params.id };
  res.json(connections[idx]);
});

router.delete("/connections/:id", (req, res) => {
  const idx = connections.findIndex(c => c.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Connection not found" });
  connections.splice(idx, 1);
  res.json({ status: "success", message: "Connection deleted" });
});

router.post("/test-connection", (req, res) => {
  const { type } = req.body;
  const latency = Math.floor(Math.random() * 50) + 10;
  if (type === "database" && !req.body.host) {
    return res.status(400).json({ status: "error", message: "Host is required for database connections" });
  }
  res.json({ status: "success", message: "Connection successful", latency });
});

// --- RUNS ---
router.get("/runs", (_req, res) => {
  res.json(runs);
});

router.delete("/runs/:id", (req, res) => {
  const idx = runs.findIndex(r => r.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Run not found" });
  runs.splice(idx, 1);
  res.json({ status: "success" });
});

router.get("/runs/:id", (req, res) => {
  const run = runs.find(r => r.id === req.params.id);
  if (!run) return res.status(404).json({ error: "Run not found" });
  res.json(run);
});

router.get("/runs/:id/logs", (req, res) => {
  const run = runs.find(r => r.id === req.params.id);
  if (!run) return res.status(404).json({ error: "Run not found" });
  res.json([
    { timestamp: run.startTime, level: "INFO", message: `Starting pipeline run for ${run.city}` },
    { timestamp: new Date(new Date(run.startTime).getTime() + 5000).toISOString(), level: "INFO", message: `Connected to data source` },
    { timestamp: new Date(new Date(run.startTime).getTime() + 30000).toISOString(), level: "INFO", message: `Collected ${run.recordsExtracted} records` },
    { timestamp: run.endTime || new Date().toISOString(), level: run.status === "failed" ? "ERROR" : "INFO", message: run.logSummary },
  ]);
});

router.get("/runs/:id/requests", (req, res) => {
  const run = runs.find(r => r.id === req.params.id);
  if (!run) return res.status(404).json({ error: "Run not found" });
  res.json([
    { id: 1, method: "GET", url: `/api/places?city=${run.city}`, status: 200, duration: 123, timestamp: run.startTime },
    { id: 2, method: "POST", url: "/api/pipeline/run", status: 200, duration: 45, timestamp: run.startTime },
  ]);
});

router.post("/execute-run", (req, res) => {
  const { connectionId } = req.body;
  const conn = connections.find(c => c.id === connectionId);
  const run = {
    id: makeId("run"),
    connectionId: connectionId || "conn-1",
    connectionName: conn?.name || "Unknown",
    status: "running",
    startTime: new Date().toISOString(),
    endTime: null,
    recordsExtracted: 0,
    logSummary: "Pipeline started",
    city: "hanoi",
    type: "restaurant"
  };
  runs.unshift(run as typeof runs[0]);
  res.status(201).json(run);
});

// --- SCHEDULES ---
router.get("/schedules", (_req, res) => {
  res.json(schedules);
});

router.put("/schedules/:id", (req, res) => {
  const idx = schedules.findIndex(s => s.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Schedule not found" });
  schedules[idx] = { ...schedules[idx], ...req.body, id: req.params.id };
  res.json(schedules[idx]);
});

router.delete("/schedules/:id", (req, res) => {
  const idx = schedules.findIndex(s => s.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Schedule not found" });
  schedules.splice(idx, 1);
  res.json({ status: "success" });
});

// --- REPORTS ---
router.get("/reports", (_req, res) => {
  res.json(reports);
});

router.get("/reports/:id", (req, res) => {
  const report = reports.find(r => r.id === req.params.id);
  if (!report) return res.status(404).json({ error: "Report not found" });
  res.json(report);
});

router.put("/reports/:id", (req, res) => {
  const idx = reports.findIndex(r => r.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Report not found" });
  reports[idx] = { ...reports[idx], ...req.body, id: req.params.id };
  res.json(reports[idx]);
});

router.post("/reports/:id/refresh", (req, res) => {
  const report = reports.find(r => r.id === req.params.id);
  if (!report) return res.status(404).json({ error: "Report not found" });
  report.status = "generating";
  setTimeout(() => {
    report.status = "ready";
    report.lastRefreshed = new Date().toISOString();
  }, 3000);
  res.json({ status: "success", message: "Report refresh started" });
});

router.delete("/reports/:id", (req, res) => {
  const idx = reports.findIndex(r => r.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Report not found" });
  reports.splice(idx, 1);
  res.json({ status: "success" });
});

// --- USERS & ROLES (Admin) ---
router.get("/users", (_req, res) => {
  res.json(users);
});

router.put("/users/:id", (req, res) => {
  const idx = users.findIndex(u => u.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "User not found" });
  users[idx] = { ...users[idx], ...req.body, id: req.params.id };
  res.json(users[idx]);
});

router.delete("/users/:id", (req, res) => {
  const idx = users.findIndex(u => u.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "User not found" });
  users.splice(idx, 1);
  res.json({ status: "success", message: "User deleted" });
});

router.get("/roles", (_req, res) => {
  res.json(roles);
});

router.put("/roles/:id", (req, res) => {
  const idx = roles.findIndex(r => r.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Role not found" });
  roles[idx] = { ...roles[idx], ...req.body, id: req.params.id };
  res.json(roles[idx]);
});

router.delete("/roles/:id", (req, res) => {
  const idx = roles.findIndex(r => r.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Role not found" });
  roles.splice(idx, 1);
  res.json({ status: "success" });
});

// --- API KEYS ---
router.get("/keys/rapidapi", (_req, res) => {
  res.json(apiKeys);
});

router.post("/keys/rapidapi", (req, res) => {
  const newKey = {
    id: apiKeys.length + 1,
    key: req.body.key,
    short_key: `${(req.body.key || "").slice(0, 8)}...`,
    label: req.body.label || `RAPID_API_KEY${apiKeys.length + 1}`,
    status: "Ready",
    status_code: 200,
    createdAt: new Date().toISOString()
  };
  apiKeys.push(newKey);
  res.status(201).json({ status: "success", message: "Key added", key: newKey });
});

router.delete("/keys/rapidapi/:id", (req, res) => {
  const id = Number(req.params.id);
  const idx = apiKeys.findIndex(k => k.id === id);
  if (idx === -1) return res.status(404).json({ error: "Key not found" });
  apiKeys.splice(idx, 1);
  res.json({ status: "success", message: "Key deleted" });
});

// --- BACKUPS ---
router.get("/backups", (_req, res) => {
  res.json(backups);
});

router.post("/backups", (_req, res) => {
  const backup = {
    id: makeId("bkp"),
    name: `manual_backup_${new Date().toISOString().replace(/[:.]/g, "").slice(0, 15)}.sql`,
    size: 0,
    createdAt: new Date().toISOString(),
    status: "processing"
  };
  backups.push(backup);
  setTimeout(() => {
    backup.status = "completed";
    backup.size = Math.floor(Math.random() * 10000000) + 50000000;
  }, 3000);
  res.status(201).json(backup);
});

router.post("/backups/:id/restore", (req, res) => {
  const backup = backups.find(b => b.id === req.params.id);
  if (!backup) return res.status(404).json({ error: "Backup not found" });
  res.json({ status: "success", message: `Restore from ${backup.name} started` });
});

router.delete("/backups/:id", (req, res) => {
  const idx = backups.findIndex(b => b.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Backup not found" });
  backups.splice(idx, 1);
  res.json({ status: "success" });
});

// --- EXPORTS ---
router.get("/exports", (_req, res) => {
  res.json(exports_);
});

router.post("/data/export", (req, res) => {
  const exp = {
    id: makeId("exp"),
    name: req.body.filename || `export_${Date.now()}.json`,
    format: req.body.format || "json",
    status: "processing",
    size: 0,
    createdAt: new Date().toISOString(),
    connectionId: req.body.connectionId || "conn-1"
  };
  exports_.push(exp as typeof exports_[0]);
  setTimeout(() => {
    (exp as { status: string }).status = "ready";
    (exp as { size: number }).size = Math.floor(Math.random() * 5000000) + 1000000;
  }, 2000);
  res.status(201).json(exp);
});

router.get("/exports/:id/download", (req, res) => {
  const exp = exports_.find(e => e.id === req.params.id);
  if (!exp) return res.status(404).json({ error: "Export not found" });
  res.setHeader("Content-Disposition", `attachment; filename="${exp.name}"`);
  res.setHeader("Content-Type", "application/json");
  res.json({ export: exp.name, data: [], generatedAt: new Date().toISOString() });
});

router.get("/data/export/:id", (req, res) => {
  const exp = exports_.find(e => e.id === req.params.id);
  if (!exp) return res.status(404).json({ error: "Export not found" });
  res.json(exp);
});

router.delete("/exports/:id", (req, res) => {
  const idx = exports_.findIndex(e => e.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Export not found" });
  exports_.splice(idx, 1);
  res.json({ status: "success" });
});

// --- MAPPINGS ---
router.get("/mappings", (_req, res) => {
  res.json(mappings);
});

// --- PARAMETER MODES ---
router.get("/parameter-modes", (_req, res) => {
  res.json(parameterModes);
});

router.put("/parameter-modes/:id", (req, res) => {
  const idx = parameterModes.findIndex(m => m.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Parameter mode not found" });
  parameterModes[idx] = { ...parameterModes[idx], ...req.body, id: req.params.id };
  res.json(parameterModes[idx]);
});

router.delete("/parameter-modes/:id", (req, res) => {
  const idx = parameterModes.findIndex(m => m.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Parameter mode not found" });
  parameterModes.splice(idx, 1);
  res.json({ status: "success" });
});

// --- OSM CONFIG ---
router.get("/osm/config", (_req, res) => {
  res.json(osmConfig);
});

router.put("/osm/config", (req, res) => {
  osmConfig = { ...osmConfig, ...req.body };
  res.json({ status: "success", message: "OSM configuration updated", config: osmConfig });
});

// --- ENRICHMENT CONFIG ---
router.get("/enrichment/config", (_req, res) => {
  res.json(enrichmentConfig);
});

router.put("/enrichment/config", (req, res) => {
  enrichmentConfig = { ...enrichmentConfig, ...req.body };
  res.json({ status: "success", message: "Enrichment configuration updated", config: enrichmentConfig });
});

// --- PIPELINE ---
router.get("/pipeline/status", (_req, res) => {
  res.json({
    status: "running",
    activeRuns: runs.filter(r => r.status === "running").length,
    queuedRuns: 0,
    lastRun: runs[0]?.startTime || null,
    nextScheduled: schedules.find(s => s.status === "active")?.nextRun || null
  });
});

router.get("/pipeline/runs", (_req, res) => {
  res.json(runs);
});

router.post("/pipeline/run", (req, res) => {
  const run = {
    id: makeId("run"),
    connectionId: req.body.connectionId || "conn-1",
    connectionName: "Manual Run",
    status: "running",
    startTime: new Date().toISOString(),
    endTime: null,
    recordsExtracted: 0,
    logSummary: "Pipeline started manually",
    city: req.body.city || "hanoi",
    type: req.body.type || "restaurant"
  };
  runs.unshift(run as typeof runs[0]);
  res.status(201).json({ run_id: run.id, status: "started" });
});

// --- DASHBOARD ---
router.get("/dashboard/pipeline-metrics", (_req, res) => {
  const now = Date.now();
  const history = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(now - (6 - i) * 86400000);
    return {
      date: d.toISOString().slice(0, 10),
      successRate: 95 + Math.random() * 4,
      runs: Math.floor(Math.random() * 5) + 2,
      avgDuration: Math.floor(Math.random() * 300) + 120
    };
  });
  res.json({
    totalRuns: runs.length,
    successRate: 92.4,
    avgDuration: 245,
    lastRun: runs[0]?.startTime || null,
    history
  });
});

// --- ANALYTICS ---
router.get("/analytics/success-rate-history", (req, res) => {
  const days = Number(req.query.days) || 7;
  const now = Date.now();
  const data = Array.from({ length: days }, (_, i) => {
    const d = new Date(now - (days - 1 - i) * 86400000);
    return {
      date: d.toISOString().slice(0, 10),
      successRate: 95 + (i % 2) - (i % 3) / 10
    };
  });
  res.json({ data });
});

// --- AIRFLOW ---
router.get("/airflow/stats", (_req, res) => {
  res.json({
    totalDAGs: airflowDags.length,
    runningDAGs: airflowDags.filter(d => !d.isPaused).length,
    successRate: 98.2,
    failedRuns: 0,
    lastRun: airflowDags[0].lastRun
  });
});

router.get("/airflow/dags", (_req, res) => {
  res.json(airflowDags);
});

router.post("/airflow/dags/:dagId/trigger", (req, res) => {
  const dag = airflowDags.find(d => d.dagId === req.params.dagId);
  if (!dag) return res.status(404).json({ error: "DAG not found" });
  dag.lastRun = new Date().toISOString();
  res.json({ status: "success", message: `DAG ${req.params.dagId} triggered`, dagRunId: makeId("dag-run") });
});

router.post("/airflow/dags/:dagId/pause", (req, res) => {
  const dag = airflowDags.find(d => d.dagId === req.params.dagId);
  if (!dag) return res.status(404).json({ error: "DAG not found" });
  dag.isPaused = true;
  dag.isActive = false;
  res.json({ status: "success" });
});

router.post("/airflow/dags/:dagId/resume", (req, res) => {
  const dag = airflowDags.find(d => d.dagId === req.params.dagId);
  if (!dag) return res.status(404).json({ error: "DAG not found" });
  dag.isPaused = false;
  dag.isActive = true;
  res.json({ status: "success" });
});

router.get("/airflow/runs", (_req, res) => {
  res.json(airflowDags.map((d, i) => ({
    runId: makeId("airflow-run"),
    dagId: d.dagId,
    status: d.isPaused ? "skipped" : "success",
    executionDate: d.lastRun,
    duration: Math.floor(Math.random() * 300) + 30
  })));
});

// --- SYSTEM SETTINGS ---
let systemSettings = {
  siteName: "SmartTravel Data Platform",
  timezone: "UTC",
  logLevel: "INFO",
  maxConcurrentRuns: 3,
  dataRetentionDays: 90,
  notificationsEnabled: true,
  maintenanceMode: false
};

router.get("/system/settings", (_req, res) => {
  res.json(systemSettings);
});

router.put("/system/settings", (req, res) => {
  systemSettings = { ...systemSettings, ...req.body };
  res.json({ status: "success", message: "Settings updated", settings: systemSettings });
});

export default router;
