import { AppErrorBoundary } from "./components/layout/AppErrorBoundary";
import { Layout } from "./components/layout/Layout";
import { TabsView } from "./components/dashboard/TabsView";
import { useDashboardEvents } from "./hooks/useDashboardEvents";

export default function App() {
  const events = useDashboardEvents();

  return (
    <AppErrorBoundary>
      <Layout isConnected={events.isConnected} error={events.error}>
        <TabsView
          alerts={events.alerts}
          correlations={events.correlations}
          snapshots={events.snapshots}
          decisions={events.decisions}
          tensions={events.tensions}
          narratives={events.narratives}
          isConnected={events.isConnected}
        />
      </Layout>
    </AppErrorBoundary>
  );
}

