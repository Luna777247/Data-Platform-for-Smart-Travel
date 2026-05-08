import { Switch, Route, Router as WouterRouter, useLocation } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { lazy, Suspense } from "react";
import { AppSidebar } from "@/components/layout/app-sidebar";
import NotFound from "@/pages/not-found";

const Home = lazy(() => import("@/pages/home"));
const Admin = lazy(() => import("@/pages/admin"));
const Airflow = lazy(() => import("@/pages/airflow"));
const Analytics = lazy(() => import("@/pages/analytics"));
const Connections = lazy(() => import("@/pages/connections"));
const ConnectionsNew = lazy(() => import("@/pages/connections-new"));
const ConnectionDetail = lazy(() => import("@/pages/connection-detail"));
const ConnectionEdit = lazy(() => import("@/pages/connection-edit"));
const Dashboards = lazy(() => import("@/pages/dashboards"));
const DashboardSmartTravel = lazy(() => import("@/pages/dashboard-smart-travel"));
const DashboardPipelineMonitor = lazy(() => import("@/pages/dashboard-pipeline-monitor"));
const Data = lazy(() => import("@/pages/data"));
const Exports = lazy(() => import("@/pages/exports"));
const Mappings = lazy(() => import("@/pages/mappings"));
const Monitoring = lazy(() => import("@/pages/monitoring"));
const ParameterModes = lazy(() => import("@/pages/parameter-modes"));
const PipelineMonitor = lazy(() => import("@/pages/pipeline-monitor"));
const Runs = lazy(() => import("@/pages/runs"));
const RunsStarting = lazy(() => import("@/pages/runs-starting"));
const RunDetail = lazy(() => import("@/pages/run-detail"));
const Schedules = lazy(() => import("@/pages/schedules"));
const Reports = lazy(() => import("@/pages/reports"));
const ReportNew = lazy(() => import("@/pages/report-new"));
const ReportDetail = lazy(() => import("@/pages/report-detail"));
const ReportEdit = lazy(() => import("@/pages/report-edit"));

const queryClient = new QueryClient();

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>
  );
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-background">
      <AppSidebar />
      <main className="flex-1 ml-64 overflow-auto">
        {children}
      </main>
    </div>
  );
}

function Router() {
  return (
    <Layout>
      <Suspense fallback={<PageLoader />}>
        <Switch>
          <Route path="/" component={Home} />
          <Route path="/admin" component={Admin} />
          <Route path="/airflow" component={Airflow} />
          <Route path="/analytics" component={Analytics} />
          <Route path="/connections" component={Connections} />
          <Route path="/connections/new" component={ConnectionsNew} />
          <Route path="/connections/:id/edit" component={ConnectionEdit} />
          <Route path="/connections/:id" component={ConnectionDetail} />
          <Route path="/dashboards" component={Dashboards} />
          <Route path="/dashboards/smart-travel" component={DashboardSmartTravel} />
          <Route path="/dashboards/pipeline-monitor" component={DashboardPipelineMonitor} />
          <Route path="/data" component={Data} />
          <Route path="/exports" component={Exports} />
          <Route path="/mappings" component={Mappings} />
          <Route path="/monitoring" component={Monitoring} />
          <Route path="/parameter-modes" component={ParameterModes} />
          <Route path="/pipeline-monitor" component={PipelineMonitor} />
          <Route path="/runs" component={Runs} />
          <Route path="/runs/starting" component={RunsStarting} />
          <Route path="/runs/:id" component={RunDetail} />
          <Route path="/schedules" component={Schedules} />
          <Route path="/reports" component={Reports} />
          <Route path="/reports/new" component={ReportNew} />
          <Route path="/reports/:id/edit" component={ReportEdit} />
          <Route path="/reports/:id" component={ReportDetail} />
          <Route component={NotFound} />
        </Switch>
      </Suspense>
    </Layout>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <Router />
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
