import { Router } from "express";

const router = Router();

const startTime = Date.now();

const connections = [
  { id: "conn-1", name: "MongoDB Atlas", type: "database", status: "connected", isActive: true, host: "cluster0.mongodb.net", port: 27017, database: "smarttravel", username: "admin", description: "Primary data store for travel POI data", lastUsed: new Date().toISOString(), lastUsedAt: new Date().toISOString(), createdAt: new Date(Date.now() - 86400000 * 10).toISOString() },
  { id: "conn-2", name: "OpenStreetMap Overpass API", type: "api", status: "connected", isActive: true, host: "overpass-api.de", port: 443, database: "", username: "", description: "OSM data collection via Overpass API", lastUsed: new Date().toISOString(), lastUsedAt: new Date().toISOString(), createdAt: new Date(Date.now() - 86400000 * 8).toISOString() },
  { id: "conn-3", name: "Google Places API", type: "api", status: "connected", isActive: true, host: "maps.googleapis.com", port: 443, database: "", username: "", description: "Place enrichment via Google Places", lastUsed: new Date().toISOString(), lastUsedAt: new Date().toISOString(), createdAt: new Date(Date.now() - 86400000 * 7).toISOString() },
  { id: "conn-4", name: "PostgreSQL Analytics", type: "database", status: "disconnected", isActive: false, host: "localhost", port: 5432, database: "analytics", username: "postgres", description: "Analytics data warehouse", lastUsed: new Date(Date.now() - 86400000 * 2).toISOString(), lastUsedAt: new Date(Date.now() - 86400000 * 2).toISOString(), createdAt: new Date(Date.now() - 86400000 * 5).toISOString() },
  { id: "conn-5", name: "Redis Cache", type: "cache", status: "connected", isActive: true, host: "localhost", port: 6379, database: "", username: "", description: "Caching layer for API responses", lastUsed: new Date().toISOString(), lastUsedAt: new Date().toISOString(), createdAt: new Date(Date.now() - 86400000 * 3).toISOString() },
];

const runs = [
  { id: "run-1", connectionId: "conn-1", connectionName: "MongoDB Atlas", status: "success", startedAt: new Date(Date.now() - 3600000).toISOString(), completedAt: new Date(Date.now() - 3300000).toISOString(), executionTime: 300000, totalRequests: 154, successfulRequests: 154, failedRequests: 0, recordsProcessed: 15420, logSummary: "Successfully processed 15420 records for hanoi" },
  { id: "run-2", connectionId: "conn-2", connectionName: "OpenStreetMap Overpass API", status: "success", startedAt: new Date(Date.now() - 7200000).toISOString(), completedAt: new Date(Date.now() - 6800000).toISOString(), executionTime: 400000, totalRequests: 89, successfulRequests: 89, failedRequests: 0, recordsProcessed: 8930, logSummary: "Extracted 8930 POIs from OSM for hcmc" },
  { id: "run-3", connectionId: "conn-3", connectionName: "Google Places API", status: "failed", startedAt: new Date(Date.now() - 10800000).toISOString(), completedAt: new Date(Date.now() - 10600000).toISOString(), executionTime: 200000, totalRequests: 12, successfulRequests: 8, failedRequests: 4, recordsProcessed: 0, logSummary: "API rate limit exceeded" },
  { id: "run-4", connectionId: "conn-1", connectionName: "MongoDB Atlas", status: "success", startedAt: new Date(Date.now() - 86400000).toISOString(), completedAt: new Date(Date.now() - 86000000).toISOString(), executionTime: 400000, totalRequests: 221, successfulRequests: 221, failedRequests: 0, recordsProcessed: 22100, logSummary: "Full sync completed for hue" },
  { id: "run-5", connectionId: "conn-2", connectionName: "OpenStreetMap Overpass API", status: "running", startedAt: new Date(Date.now() - 1800000).toISOString(), completedAt: null, executionTime: null, totalRequests: 42, successfulRequests: 42, failedRequests: 0, recordsProcessed: 4210, logSummary: "In progress: collecting data for quangnam" },
];

const schedules = [
  { id: "sched-1", connectionId: "conn-1", connectionName: "MongoDB Atlas", name: "Daily Hanoi Sync", description: "Daily full sync for Hanoi POI data", status: "active", isActive: true, scheduleType: "daily", frequency: "daily", cronExpression: "0 2 * * *", nextRun: new Date(Date.now() + 3600000 * 6).toISOString(), lastRun: new Date(Date.now() - 3600000).toISOString(), lastStatus: "success", totalRuns: 47 },
  { id: "sched-2", connectionId: "conn-2", connectionName: "OSM Overpass API", name: "Weekly OSM Full Scan", description: "Weekly full OSM data collection scan", status: "active", isActive: true, scheduleType: "weekly", frequency: "weekly", cronExpression: "0 1 * * 0", nextRun: new Date(Date.now() + 86400000 * 5).toISOString(), lastRun: new Date(Date.now() - 86400000 * 2).toISOString(), lastStatus: "success", totalRuns: 18 },
  { id: "sched-3", connectionId: "conn-3", connectionName: "Google Places API", name: "Google Enrichment", description: "Daily Google Places enrichment run", status: "paused", isActive: false, scheduleType: "daily", frequency: "daily", cronExpression: "0 4 * * *", nextRun: null, lastRun: new Date(Date.now() - 86400000 * 3).toISOString(), lastStatus: "failed", totalRuns: 12 },
  { id: "sched-4", connectionId: "conn-4", connectionName: "PostgreSQL Analytics", name: "Analytics Rollup", description: "Hourly analytics aggregation rollup", status: "active", isActive: true, scheduleType: "cron", frequency: "hourly", cronExpression: "0 * * * *", nextRun: new Date(Date.now() + 3600000).toISOString(), lastRun: new Date(Date.now() - 3600000).toISOString(), lastStatus: "success", totalRuns: 320 },
  { id: "sched-5", connectionId: "conn-5", connectionName: "Redis Cache", name: "Cache Warmup", description: "Daily cache warmup job", status: "active", isActive: true, scheduleType: "daily", frequency: "daily", cronExpression: "30 0 * * *", nextRun: new Date(Date.now() + 3600000 * 18).toISOString(), lastRun: new Date(Date.now() - 3600000 * 6).toISOString(), lastStatus: "success", totalRuns: 89 },
];

const reports = [
  { id: "rpt-1", name: "Monthly Travel Summary", description: "Monthly analytics report for all cities", type: "analytics", status: "ready", lastRefreshed: new Date(Date.now() - 3600000 * 2).toISOString(), createdAt: new Date(Date.now() - 86400000 * 30).toISOString(), data: { totalPlaces: 48231, avgRating: 4.2, topCity: "Hanoi" } },
  { id: "rpt-2", name: "API Key Health Report", description: "Status and usage of all RapidAPI keys", type: "system", status: "ready", lastRefreshed: new Date(Date.now() - 3600000).toISOString(), createdAt: new Date(Date.now() - 86400000 * 15).toISOString(), data: { totalKeys: 5, activeKeys: 4, blockedKeys: 1 } },
  { id: "rpt-3", name: "Pipeline Performance", description: "Pipeline execution metrics and trends", type: "performance", status: "generating", lastRefreshed: null, createdAt: new Date(Date.now() - 86400000 * 7).toISOString(), data: null },
];

const users = [
  { id: "usr-1", email: "admin@smarttravel.io", name: "Admin User", role: "admin", status: "active", isActive: true, lastLogin: new Date(Date.now() - 3600000).toISOString(), createdAt: new Date(Date.now() - 86400000 * 60).toISOString() },
  { id: "usr-2", email: "analyst@smarttravel.io", name: "Data Analyst", role: "analyst", status: "active", isActive: true, lastLogin: new Date(Date.now() - 86400000).toISOString(), createdAt: new Date(Date.now() - 86400000 * 30).toISOString() },
  { id: "usr-3", email: "viewer@smarttravel.io", name: "Report Viewer", role: "viewer", status: "inactive", isActive: false, lastLogin: new Date(Date.now() - 86400000 * 14).toISOString(), createdAt: new Date(Date.now() - 86400000 * 20).toISOString() },
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

const exports_: Array<{ id: string; name: string; format: string; status: string; size: number; createdAt: string; connectionId: string }> = [
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
  cities: {
    hanoi: { name: "Thành phố Hà Nội", bbox: "20.7,105.7,21.3,106.0" },
    hcmc: { name: "Thành phố Hồ Chí Minh", bbox: "10.5,106.4,11.0,106.9" },
    danang: { name: "Thành phố Đà Nẵng", bbox: "" }
  },
  overpass_urls: ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
};

let enrichmentConfig = {
  fields: "name,rating,user_ratings_total,photos,opening_hours",
  language: "vi",
  smart_delay: 2.0,
  daily_limit: 500
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
  const completedRuns = runs.filter(r => r.status === "success").length;
  const successRate = totalRuns > 0 ? Math.round((completedRuns / totalRuns) * 100 * 10) / 10 : 0;
  res.json({
    status: "healthy",
    health: "healthy",
    uptime: getUptimeString(),
    activeUsers: users.filter(u => u.isActive).length,
    totalConnections: connections.length,
    connections: { active: connections.filter(c => c.isActive).length, total: connections.length },
    schedules: { total: schedules.length, active: schedules.filter(s => s.isActive).length },
    runs: { total: totalRuns, last24h: runs.filter(r => new Date(r.startedAt) > new Date(Date.now() - 86400000)).length },
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
  const conn = {
    id: makeId("conn"),
    createdAt: new Date().toISOString(),
    lastUsed: new Date().toISOString(),
    lastUsedAt: new Date().toISOString(),
    status: "disconnected",
    isActive: false,
    ...req.body
  };
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
  const latency = Math.floor(Math.random() * 50) + 10;
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
    { timestamp: run.startedAt, level: "INFO", message: `Starting pipeline run` },
    { timestamp: new Date(new Date(run.startedAt).getTime() + 5000).toISOString(), level: "INFO", message: "Connected to data source" },
    { timestamp: new Date(new Date(run.startedAt).getTime() + 30000).toISOString(), level: "INFO", message: `Processed ${run.recordsProcessed} records` },
    { timestamp: run.completedAt || new Date().toISOString(), level: run.status === "failed" ? "ERROR" : "INFO", message: run.logSummary },
  ]);
});

router.get("/runs/:id/requests", (req, res) => {
  const run = runs.find(r => r.id === req.params.id);
  if (!run) return res.status(404).json({ error: "Run not found" });
  res.json([
    { id: 1, method: "GET", url: "/api/places", status: 200, duration: 123, timestamp: run.startedAt },
    { id: 2, method: "POST", url: "/api/pipeline/run", status: 200, duration: 45, timestamp: run.startedAt },
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
    startedAt: new Date().toISOString(),
    completedAt: null,
    executionTime: null,
    totalRequests: 0,
    successfulRequests: 0,
    failedRequests: 0,
    recordsProcessed: 0,
    logSummary: "Pipeline started"
  };
  runs.unshift(run as typeof runs[0]);
  res.status(201).json(run);
});

// --- SCHEDULES ---
router.get("/schedules", (_req, res) => {
  res.json(schedules);
});

router.post("/schedules", (req, res) => {
  const conn = connections.find(c => c.id === req.body.connectionId);
  const sched = {
    id: makeId("sched"),
    connectionId: req.body.connectionId || "",
    connectionName: conn?.name || req.body.connectionName || "",
    name: req.body.name || req.body.connectionName || "New Schedule",
    description: req.body.description || "",
    status: "active",
    isActive: req.body.isActive !== false,
    scheduleType: req.body.scheduleType || "cron",
    frequency: req.body.scheduleType || "daily",
    cronExpression: req.body.cronExpression || "0 0 * * *",
    nextRun: new Date(Date.now() + 86400000).toISOString(),
    lastRun: null,
    lastStatus: null,
    totalRuns: 0
  };
  schedules.push(sched as typeof schedules[0]);
  res.status(201).json(sched);
});

router.put("/schedules/:id", (req, res) => {
  const idx = schedules.findIndex(s => s.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "Schedule not found" });
  const updated = { ...schedules[idx], ...req.body, id: req.params.id };
  if (typeof req.body.isActive === "boolean") {
    updated.status = req.body.isActive ? "active" : "paused";
  }
  schedules[idx] = updated as typeof schedules[0];
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

router.post("/users", (req, res) => {
  const user = {
    id: makeId("usr"),
    email: req.body.email || "",
    name: req.body.name || "",
    role: req.body.role || "user",
    status: req.body.isActive !== false ? "active" : "inactive",
    isActive: req.body.isActive !== false,
    lastLogin: null,
    createdAt: new Date().toISOString()
  };
  users.push(user as typeof users[0]);
  res.status(201).json(user);
});

router.put("/users/:id", (req, res) => {
  const idx = users.findIndex(u => u.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "User not found" });
  const updated = { ...users[idx], ...req.body, id: req.params.id };
  if (typeof req.body.isActive === "boolean") {
    updated.status = req.body.isActive ? "active" : "inactive";
  }
  users[idx] = updated as typeof users[0];
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

router.post("/roles", (req, res) => {
  const role = {
    id: makeId("role"),
    name: req.body.name || "",
    description: req.body.description || "",
    permissions: req.body.permissions || []
  };
  roles.push(role);
  res.status(201).json(role);
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
    (backup as { status: string }).status = "completed";
    (backup as { size: number }).size = Math.floor(Math.random() * 10000000) + 50000000;
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
  exports_.push(exp);
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
    lastRun: runs[0]?.startedAt || null,
    nextScheduled: schedules.find(s => s.isActive)?.nextRun || null
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
    startedAt: new Date().toISOString(),
    completedAt: null,
    executionTime: null,
    totalRequests: 0,
    successfulRequests: 0,
    failedRequests: 0,
    recordsProcessed: 0,
    logSummary: "Pipeline started manually"
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
    lastRun: runs[0]?.startedAt || null,
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
  res.json(airflowDags.map(d => ({
    runId: `run-${d.dagId}-${Date.now()}`,
    dagId: d.dagId,
    status: d.isPaused ? "skipped" : "success",
    startDate: d.lastRun,
    executionDate: d.lastRun,
    duration: Math.floor(Math.random() * 300) + 30,
    successTasks: d.isPaused ? 0 : Math.floor(Math.random() * 8) + 2,
    failedTasks: d.isPaused ? 0 : (Math.random() > 0.8 ? 1 : 0),
  })));
});

// --- ANALYTICS ---
router.get("/analytics", (_req, res) => {
  const allRuns = runs;
  const successCount = allRuns.filter(r => r.status === "success").length;
  const failedCount = allRuns.filter(r => r.status === "failed").length;
  const runningCount = allRuns.filter(r => r.status === "running").length;
  const totalCount = allRuns.length;
  const successRate = totalCount > 0 ? (successCount / totalCount) * 100 : 0;
  const runs24h = allRuns.filter(r => new Date(r.startedAt).getTime() > Date.now() - 86400000).length;

  const successRateHistory = Array.from({ length: 30 }, (_, i) => {
    const d = new Date(Date.now() - (29 - i) * 86400000);
    const dateStr = d.toISOString().slice(0, 10);
    return { date: dateStr, successRate: Math.round(85 + Math.random() * 15) };
  });

  const dailyActivity = Array.from({ length: 30 }, (_, i) => {
    const d = new Date(Date.now() - (29 - i) * 86400000);
    const dateStr = d.toISOString().slice(0, 10);
    return { date: dateStr, runs: Math.floor(2 + Math.random() * 12) };
  });

  const connectionCounts: Record<string, number> = {};
  allRuns.forEach(r => {
    connectionCounts[r.connectionName] = (connectionCounts[r.connectionName] || 0) + 1;
  });
  const runsByConnection = Object.entries(connectionCounts).map(([name, value]) => ({ name, value }));

  const statusDistribution = [
    { name: "Success", value: successCount },
    { name: "Failed", value: failedCount },
    { name: "Running", value: runningCount },
  ].filter(s => s.value > 0);

  const completedRuns = allRuns.filter(r => r.executionTime != null);
  const avgResponseTime = completedRuns.length > 0
    ? Math.round(completedRuns.reduce((sum, r) => sum + (r.executionTime || 0), 0) / completedRuns.length / 1000)
    : 0;

  res.json({
    summary: {
      totalRuns: totalCount,
      successRate: parseFloat(successRate.toFixed(2)),
      avgResponseTime,
      runsLast24h: runs24h,
    },
    successRateHistory,
    dailyActivity,
    runsByConnection,
    statusDistribution,
  });
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
