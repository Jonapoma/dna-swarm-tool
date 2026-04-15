<template>
  <div class="sim-view">
    <!-- Header -->
    <div class="sim-header">
      <router-link to="/" class="back-link">← New Simulation</router-link>
      <div class="sim-title">
        <h2>
          {{ trialConfig?.drug || '...' }}
          <span v-if="trialConfig">{{ trialConfig.dose_mg }}mg · {{ trialConfig.route }}</span>
        </h2>
        <span class="badge" :class="statusBadge">{{ store.simulationStatus }}</span>
      </div>
      <div class="sim-meta" v-if="trialConfig">
        {{ trialConfig.indication }} · {{ trialConfig.duration_days }} days · {{ store.totalAgents }} agents
      </div>
    </div>

    <!-- Progress -->
    <div v-if="store.simulationStatus === 'running'" class="progress-section card">
      <div class="progress-header">
        <span>Running agents...</span>
        <span>{{ store.completedAgents }} / {{ store.totalAgents }}</span>
      </div>
      <div class="progress-bar-wrap">
        <div class="progress-bar" :style="{ width: store.progress + '%' }"></div>
      </div>
      <div class="progress-sub">{{ store.progress }}% complete · Claude API active</div>
    </div>

    <!-- Error -->
    <div v-if="store.simulationStatus === 'failed'" class="error-box">
      Simulation failed: {{ store.error }}
    </div>

    <!-- Results -->
    <div v-if="store.simulationStatus === 'completed'">
      <!-- KPI row -->
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-val green">{{ stats.mean_efficacy_score }}<span class="kpi-unit">/10</span></div>
          <div class="kpi-label">Mean Efficacy</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-val green">{{ stats.response_rate_pct }}<span class="kpi-unit">%</span></div>
          <div class="kpi-label">Endpoint Rate</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-val yellow">{{ stats.adr_rate_pct }}<span class="kpi-unit">%</span></div>
          <div class="kpi-label">ADR Rate</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-val red">{{ stats.discontinuation_rate_pct }}<span class="kpi-unit">%</span></div>
          <div class="kpi-label">Discontinuation</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-val purple">{{ stats.total_agents }}</div>
          <div class="kpi-label">Agents</div>
        </div>
      </div>

      <!-- Charts row -->
      <div class="charts-row">
        <div class="card chart-card">
          <div class="card-title">Response Distribution</div>
          <Doughnut :data="responseChartData" :options="doughnutOptions" />
        </div>
        <div class="card chart-card">
          <div class="card-title">Efficacy by Phenotype</div>
          <Bar :data="phenotypeChartData" :options="barOptions" />
        </div>
      </div>

      <!-- Phenotype table -->
      <div class="card table-card">
        <div class="card-title">PGx Subpopulation Breakdown</div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Phenotype</th><th>N</th><th>Mean Efficacy</th>
                <th>Response Rate</th><th>ADR Rate</th><th>Discontinuation</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(data, phen) in stats.phenotype_breakdown" :key="phen">
                <td>
                  <span class="badge" :class="phenotypeBadge(phen)">
                    {{ phen.replace(/_/g, ' ') }}
                  </span>
                </td>
                <td>{{ data.n }}</td>
                <td>
                  <span :class="efficacyColor(data.mean_efficacy)">{{ data.mean_efficacy }}</span>
                </td>
                <td>{{ data.response_rate_pct }}%</td>
                <td :class="data.adr_rate_pct > 30 ? 'txt-red' : ''">{{ data.adr_rate_pct }}%</td>
                <td :class="data.discontinuation_rate_pct > 10 ? 'txt-red' : ''">{{ data.discontinuation_rate_pct }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Top ADRs -->
      <div v-if="stats.top_adverse_events?.length" class="card table-card">
        <div class="card-title">Top Adverse Events</div>
        <div class="adr-bars">
          <div v-for="adr in stats.top_adverse_events.slice(0,8)" :key="adr.event" class="adr-row">
            <span class="adr-name">{{ adr.event.replace(/_/g, ' ') }}</span>
            <div class="adr-bar-wrap">
              <div class="adr-bar" :style="{ width: adr.rate_pct + '%' }"></div>
            </div>
            <span class="adr-pct">{{ adr.rate_pct }}%</span>
          </div>
        </div>
      </div>

      <!-- Population Analysis -->
      <div class="card analysis-card">
        <div class="card-title">AI Population Analysis
          <span class="badge badge-blue" style="margin-left:8px">Claude {{ store.trialConfig?.drug }}</span>
        </div>
        <div class="analysis-body" v-html="analysisHtml"></div>
      </div>

      <!-- Agent table -->
      <div class="card table-card">
        <div class="card-title">Agent Results (first {{ Math.min(store.agentResults.length, 50) }})</div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Age</th><th>Sex</th><th>Phenotype</th>
                <th>Efficacy</th><th>Response</th><th>ADRs</th><th>Endpoint</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in store.agentResults.slice(0, 50)" :key="r.patient_id">
                <td class="mono">{{ r.patient_id?.slice(0, 18) }}</td>
                <td>{{ r.age }}</td>
                <td>{{ r.sex }}</td>
                <td class="phen-cell">{{ r.phenotype?.replace(/_/g, ' ') }}</td>
                <td>
                  <span :class="efficacyColor(r.efficacy_score)">{{ r.efficacy_score }}/10</span>
                </td>
                <td>{{ r.response_category?.replace(/_/g, ' ') }}</td>
                <td class="adr-cell">{{ r.adverse_events?.slice(0,2).join(', ') || '—' }}</td>
                <td>
                  <span class="badge" :class="r.trial_endpoint_met ? 'badge-green' : 'badge-red'">
                    {{ r.trial_endpoint_met ? 'Yes' : 'No' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Download buttons -->
      <div class="download-row">
        <a :href="`/api/report/${simId}/html`" download class="btn btn-secondary">⬇ Download HTML Report</a>
        <a :href="`/api/report/${simId}/json`" download class="btn btn-secondary">⬇ Download JSON</a>
        <router-link to="/" class="btn btn-primary">+ New Simulation</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSimulationStore } from '../stores/simulation.js'
import { Doughnut, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale, BarElement, Title
} from 'chart.js'
import axios from 'axios'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title)

const route = useRoute()
const store = useSimulationStore()
const simId = route.params.id

const trialConfig = computed(() => store.trialConfig)
const stats = computed(() => store.statistics || {})

onMounted(async () => {
  if (store.simulationId !== simId) {
    // Restore from API if navigated directly
    try {
      const { data } = await axios.get(`/api/simulation/status/${simId}`)
      store.simulationId = simId
      store.simulationStatus = data.status
      store.progress = data.progress_pct
      store.completedAgents = data.completed_agents
      store.totalAgents = data.total_agents
      if (data.status === 'running') {
        store._startPolling()
      } else if (data.status === 'completed') {
        const res = await axios.get(`/api/simulation/result/${simId}`)
        store.statistics = res.data.statistics
        store.populationAnalysis = res.data.population_analysis
        store.trialConfig = res.data.trial_config
        const agents = await axios.get(`/api/simulation/result/${simId}/agents?limit=200`)
        store.agentResults = agents.data.results
      }
    } catch {}
  }
})

onUnmounted(() => {
  if (store.pollTimer) clearInterval(store.pollTimer)
})

const statusBadge = computed(() => {
  const s = store.simulationStatus
  return s === 'completed' ? 'badge-green' : s === 'failed' ? 'badge-red' : 'badge-yellow'
})

const PALETTE = ['#58a6ff','#3fb950','#f85149','#d29922','#bc8cff','#ffa657','#79c0ff']

const responseChartData = computed(() => {
  const dist = stats.value.response_distribution || {}
  return {
    labels: Object.keys(dist).map(k => k.replace(/_/g, ' ')),
    datasets: [{ data: Object.values(dist), backgroundColor: PALETTE, borderWidth: 0 }]
  }
})

const phenotypeChartData = computed(() => {
  const bd = stats.value.phenotype_breakdown || {}
  return {
    labels: Object.keys(bd).map(k => k.replace(/_/g, ' ')),
    datasets: [
      {
        label: 'Mean Efficacy',
        data: Object.values(bd).map(d => d.mean_efficacy),
        backgroundColor: 'rgba(88,166,255,0.7)',
        yAxisID: 'y',
      },
      {
        label: 'Response Rate %',
        data: Object.values(bd).map(d => d.response_rate_pct),
        backgroundColor: 'rgba(63,185,80,0.7)',
        yAxisID: 'y1',
      },
    ]
  }
})

const doughnutOptions = {
  responsive: true,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#8b949e', font: { size: 11 } } }
  }
}

const barOptions = {
  responsive: true,
  plugins: { legend: { labels: { color: '#8b949e', font: { size: 11 } } } },
  scales: {
    x: { ticks: { color: '#8b949e', font: { size: 9 } }, grid: { color: '#30363d' } },
    y: { ticks: { color: '#8b949e' }, grid: { color: '#30363d' }, max: 10,
         title: { display: true, text: 'Efficacy', color: '#8b949e' } },
    y1: { position: 'right', ticks: { color: '#8b949e' }, grid: { display: false }, max: 100,
          title: { display: true, text: 'Response %', color: '#8b949e' } },
  }
}

// Basic markdown → HTML
const analysisHtml = computed(() => {
  const md = store.populationAnalysis || ''
  return md
    .replace(/### (.+)/g, '<h4>$1</h4>')
    .replace(/## (.+)/g, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^- (.+)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[hul])/gm, '')
})

function phenotypeBadge(phen) {
  if (phen.includes('poor') || phen.includes('low') || phen.includes('deficient')) return 'badge-red'
  if (phen.includes('ultrarapid') || phen.includes('high')) return 'badge-yellow'
  if (phen.includes('intermediate')) return 'badge-purple'
  return 'badge-blue'
}

function efficacyColor(score) {
  if (score >= 7) return 'txt-green'
  if (score >= 4) return 'txt-yellow'
  return 'txt-red'
}
</script>

<style scoped>
.sim-view { max-width: 1000px; margin: 0 auto; }

.sim-header { margin-bottom: 20px; }
.back-link { color: var(--muted); font-size: 13px; text-decoration: none; }
.back-link:hover { color: var(--accent); }
.sim-title { display: flex; align-items: center; gap: 12px; margin: 8px 0 4px; }
.sim-title h2 { font-size: 20px; }
.sim-title h2 span { color: var(--muted); font-weight: 400; font-size: 15px; }
.sim-meta { color: var(--muted); font-size: 13px; }

.progress-section { margin-bottom: 20px; }
.progress-header { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 13px; }
.progress-bar-wrap { height: 8px; background: var(--surface2); border-radius: 4px; overflow: hidden; }
.progress-bar { height: 100%; background: var(--accent); border-radius: 4px; transition: width .3s; }
.progress-sub { font-size: 11px; color: var(--muted); margin-top: 6px; }

.kpi-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
.kpi-card {
  flex: 1; min-width: 120px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 14px 16px; text-align: center;
}
.kpi-val { font-size: 26px; font-weight: 700; }
.kpi-val.green { color: var(--green); }
.kpi-val.yellow { color: var(--yellow); }
.kpi-val.red { color: var(--red); }
.kpi-val.purple { color: var(--purple); }
.kpi-unit { font-size: 14px; font-weight: 400; color: var(--muted); }
.kpi-label { font-size: 11px; color: var(--muted); margin-top: 2px; }

.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.chart-card { padding: 16px; }
@media(max-width: 640px) { .charts-row { grid-template-columns: 1fr; } }

.card-title { font-size: 13px; font-weight: 600; color: var(--accent); margin-bottom: 14px; }
.table-card { margin-bottom: 16px; padding: 16px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--border); color: var(--muted); font-weight: 500; }
td { padding: 6px 10px; border-bottom: 1px solid var(--border); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(88,166,255,0.03); }
.mono { font-family: monospace; font-size: 11px; }
.phen-cell { max-width: 160px; word-break: break-word; }
.adr-cell { max-width: 160px; color: var(--muted); font-size: 11px; }

.adr-bars { display: flex; flex-direction: column; gap: 8px; }
.adr-row { display: flex; align-items: center; gap: 10px; font-size: 12px; }
.adr-name { width: 200px; flex-shrink: 0; color: var(--muted); }
.adr-bar-wrap { flex: 1; height: 8px; background: var(--surface2); border-radius: 4px; overflow: hidden; }
.adr-bar { height: 100%; background: var(--red); border-radius: 4px; }
.adr-pct { width: 40px; text-align: right; color: var(--text); }

.analysis-card { margin-bottom: 16px; }
.analysis-body { color: var(--muted); font-size: 13px; line-height: 1.7; }
.analysis-body :deep(h3) { color: var(--text); font-size: 14px; margin: 14px 0 6px; }
.analysis-body :deep(h4) { color: var(--text); font-size: 13px; margin: 10px 0 4px; }
.analysis-body :deep(strong) { color: var(--text); }
.analysis-body :deep(ul) { padding-left: 20px; margin-bottom: 8px; }
.analysis-body :deep(li) { margin-bottom: 3px; }
.analysis-body :deep(p) { margin-bottom: 8px; }

.download-row { display: flex; gap: 12px; margin-top: 20px; flex-wrap: wrap; }

.txt-green { color: var(--green); }
.txt-yellow { color: var(--yellow); }
.txt-red { color: var(--red); }
</style>
