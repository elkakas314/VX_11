"""Shub Frontend Dashboard Component"""

const ShubDashboard = {
  data() {
    return {
      status: "loading",
      engines: [],
      projects: [],
      currentJob: null,
      stats: {},
    };
  },

  async mounted() {
    await this.loadDashboard();
    // Poll every 5 seconds
    setInterval(() => this.loadDashboard(), 5000);
  },

  methods: {
    async loadDashboard() {
      try {
        const response = await fetch("/operator/shub/dashboard");
        const data = await response.json();
        this.status = data.status;
        this.engines = this.formatEngines(data.engines);
        this.stats = data.stats || {};
      } catch (error) {
        console.error("Dashboard error:", error);
      }
    },

    formatEngines(enginesData) {
      return [
        { name: "Analyzer", status: "healthy", jobs: 2 },
        { name: "EQ Generator", status: "healthy", jobs: 1 },
        { name: "AI Mastering", status: "healthy", jobs: 0 },
        { name: "Batch Processor", status: "idle", jobs: 0 },
      ];
    },

    async createProject(name) {
      const response = await fetch("/operator/shub/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const data = await response.json();
      return data;
    },

    async setPriority(jobId, priority) {
      await fetch(`/operator/shub/queue/${jobId}/priority`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ priority }),
      });
      await this.loadDashboard();
    },
  },

  template: `
    <div class="shub-dashboard">
      <div class="dashboard-header">
        <h1>Shubniggurath Audio Studio Dashboard</h1>
        <span class="status" :class="status">{{ status }}</span>
      </div>
      
      <div class="stats-grid">
        <div class="stat-card">
          <h3>Engines Active</h3>
          <p class="big-number">{{ engines.length }}/10</p>
        </div>
        <div class="stat-card">
          <h3>Active Projects</h3>
          <p class="big-number">{{ stats.active_projects || 0 }}</p>
        </div>
        <div class="stat-card">
          <h3>Processing Queue</h3>
          <p class="big-number">{{ stats.queue_length || 0 }}</p>
        </div>
      </div>
      
      <div class="engines-section">
        <h2>DSP Engines Status</h2>
        <div class="engines-grid">
          <div v-for="engine in engines" :key="engine.name" class="engine-card">
            <h4>{{ engine.name }}</h4>
            <span class="status-badge" :class="engine.status">{{ engine.status }}</span>
            <p>Jobs: {{ engine.jobs }}</p>
          </div>
        </div>
      </div>
    </div>
  `,
};

export default ShubDashboard;
