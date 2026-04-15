<template>
  <div class="home">
    <!-- Hero -->
    <div class="hero">
      <h1 class="hero-title">
        Simulate Drug Trials Using<br/>
        <span class="highlight">Genomic Swarm Intelligence</span>
      </h1>
      <p class="hero-sub">
        Upload a DNA cohort (23andMe / VCF) or generate a synthetic population.
        GenomicSwarm seeds autonomous patient agents with CPIC-validated
        pharmacogenomic profiles, then simulates drug responses at scale.
      </p>
      <div class="hero-stats">
        <div class="stat"><span class="stat-val">11</span><span class="stat-label">Genes covered</span></div>
        <div class="stat"><span class="stat-val">12</span><span class="stat-label">CPIC Tier A drugs</span></div>
        <div class="stat"><span class="stat-val">1000</span><span class="stat-label">Max agents / run</span></div>
        <div class="stat"><span class="stat-val">3</span><span class="stat-label">Populations</span></div>
      </div>
    </div>

    <div class="workflow-grid">
      <!-- Step 1: Cohort source -->
      <div class="card step-card" :class="{ active: step >= 1 }">
        <div class="section-title">
          <span class="step-num">1</span> Cohort Source
        </div>

        <div class="tab-row">
          <button
            class="tab-btn"
            :class="{ active: cohortMode === 'synthetic' }"
            @click="cohortMode = 'synthetic'"
          >Synthetic</button>
          <button
            class="tab-btn"
            :class="{ active: cohortMode === 'upload' }"
            @click="cohortMode = 'upload'"
          >Upload DNA File</button>
        </div>

        <!-- Synthetic -->
        <div v-if="cohortMode === 'synthetic'">
          <div class="form-grid-2">
            <div class="form-group">
              <label class="form-label">Population</label>
              <select v-model="synth.population" class="form-select">
                <option v-for="p in store.populations" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Number of Agents</label>
              <input v-model.number="synth.n_agents" type="number" min="10" max="1000" class="form-input" />
            </div>
          </div>
        </div>

        <!-- Upload -->
        <div v-else>
          <div
            class="drop-zone"
            :class="{ 'drag-over': dragging }"
            @dragover.prevent="dragging = true"
            @dragleave="dragging = false"
            @drop.prevent="onDrop"
            @click="$refs.fileInput.click()"
          >
            <input ref="fileInput" type="file" accept=".txt,.vcf,.tsv,.gz" hidden @change="onFileSelect" />
            <div v-if="!uploadFile">
              <div class="drop-icon">📂</div>
              <div class="drop-text">Drop 23andMe / VCF file here</div>
              <div class="drop-hint">Supports .txt, .vcf, .tsv, .vcf.gz</div>
            </div>
            <div v-else class="file-selected">
              <span class="file-icon">📄</span>
              <span>{{ uploadFile.name }}</span>
              <span class="file-size">({{ (uploadFile.size/1024/1024).toFixed(1) }} MB)</span>
              <button class="clear-file" @click.stop="uploadFile = null">✕</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 2: Drug Configuration -->
      <div class="card step-card" :class="{ active: step >= 1 }">
        <div class="section-title">
          <span class="step-num">2</span> Drug Trial Configuration
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">Drug</label>
            <select v-model="trial.drug" class="form-select" @change="onDrugChange">
              <option v-for="d in store.drugs" :key="d.name" :value="d.name">
                {{ d.name }} ({{ d.gene }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Dose (mg)</label>
            <input v-model.number="trial.dose_mg" type="number" min="1" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">Route</label>
            <select v-model="trial.route" class="form-select">
              <option>oral</option>
              <option>IV</option>
              <option>topical</option>
              <option>subcutaneous</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Duration (days)</label>
            <input v-model.number="trial.duration_days" type="number" min="1" class="form-input" />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Indication</label>
          <input v-model="trial.indication" type="text" class="form-input" placeholder="e.g. moderate acute pain" />
        </div>
        <div class="form-group">
          <label class="form-label">Comparator</label>
          <input v-model="trial.comparator" type="text" class="form-input" placeholder="e.g. placebo" />
        </div>

        <div v-if="selectedDrug" class="drug-info">
          <div class="drug-info-gene">
            Gene: <strong>{{ selectedDrug.gene }}</strong>
            <span class="badge badge-blue" style="margin-left:6px">CPIC {{ selectedDrug.tier }}</span>
          </div>
          <div class="drug-info-mech">{{ selectedDrug.mechanism_short }}</div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="store.error" class="error-box">{{ store.error }}</div>

    <!-- Run button -->
    <div class="run-row">
      <button
        class="btn btn-primary run-btn"
        :disabled="store.loading || !canRun"
        @click="runSimulation"
      >
        <span v-if="store.loading">⏳ Preparing...</span>
        <span v-else>🚀 Launch Simulation</span>
      </button>
      <div v-if="store.cohortMeta" class="cohort-ready">
        ✓ Cohort ready: <strong>{{ store.cohortMeta.sample_count }}</strong> agents
      </div>
    </div>

    <!-- Previous simulations -->
    <div v-if="recentSims.length" style="margin-top:32px">
      <div class="section-title" style="margin-bottom:12px">Recent Simulations</div>
      <div class="sim-list">
        <div v-for="sim in recentSims" :key="sim.id" class="sim-item" @click="goToSim(sim.id)">
          <div class="sim-item-left">
            <span class="badge" :class="statusBadge(sim.status)">{{ sim.status }}</span>
            <span class="sim-drug">{{ sim.trial_config?.drug }} {{ sim.trial_config?.dose_mg }}mg</span>
            <span class="sim-agents">{{ sim.total_agents }} agents</span>
          </div>
          <div class="sim-item-right">
            {{ formatDate(sim.started_at) }}
            <span class="arrow">→</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSimulationStore } from '../stores/simulation.js'
import axios from 'axios'

const store = useSimulationStore()
const router = useRouter()

const cohortMode = ref('synthetic')
const dragging = ref(false)
const uploadFile = ref(null)
const recentSims = ref([])
const step = ref(1)

const synth = ref({ population: 'European', n_agents: 100 })
const trial = ref({
  drug: 'codeine',
  dose_mg: 30,
  route: 'oral',
  duration_days: 14,
  indication: 'moderate acute pain',
  comparator: 'placebo',
  max_agents: 100,
})

const selectedDrug = computed(() =>
  store.drugs.find(d => d.name === trial.value.drug)
)

const canRun = computed(() => {
  if (cohortMode.value === 'upload') return !!uploadFile.value
  return synth.value.n_agents >= 10
})

onMounted(async () => {
  await Promise.all([store.fetchDrugs(), store.fetchPopulations()])
  try {
    const { data } = await axios.get('/api/simulation/list')
    recentSims.value = data.simulations.slice(0, 5).reverse()
  } catch {}
})

function onDrugChange() {
  const d = store.drugs.find(x => x.name === trial.value.drug)
  if (d) {
    const defaults = {
      codeine: { dose_mg: 30, indication: 'moderate acute pain' },
      clopidogrel: { dose_mg: 75, indication: 'acute coronary syndrome' },
      warfarin: { dose_mg: 5, indication: 'atrial fibrillation anticoagulation' },
      simvastatin: { dose_mg: 40, indication: 'hypercholesterolaemia' },
      '5-fluorouracil': { dose_mg: 500, indication: 'colorectal cancer' },
      azathioprine: { dose_mg: 2, indication: 'autoimmune disease / transplant' },
      omeprazole: { dose_mg: 20, indication: 'peptic ulcer / H. pylori eradication' },
    }
    if (defaults[d.name]) Object.assign(trial.value, defaults[d.name])
  }
}

function onFileSelect(e) {
  uploadFile.value = e.target.files[0] || null
}
function onDrop(e) {
  dragging.value = false
  uploadFile.value = e.dataTransfer.files[0] || null
}

async function runSimulation() {
  store.error = null
  try {
    if (cohortMode.value === 'upload') {
      await store.uploadCohort(uploadFile.value, trial.value.drug, trial.value.dose_mg)
    } else {
      await store.createSyntheticCohort({
        drug: trial.value.drug,
        dose_mg: trial.value.dose_mg,
        n_agents: synth.value.n_agents,
        population: synth.value.population,
      })
    }
    const sim = await store.startSimulation(trial.value)
    router.push({ name: 'simulation', params: { id: sim.simulation_id } })
  } catch (e) {
    // error shown from store
  }
}

function goToSim(id) { router.push({ name: 'simulation', params: { id } }) }

function statusBadge(s) {
  return s === 'completed' ? 'badge-green' : s === 'failed' ? 'badge-red' : 'badge-yellow'
}
function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString()
}
</script>

<style scoped>
.home { max-width: 900px; margin: 0 auto; }

.hero { text-align: center; padding: 32px 0 28px; }
.hero-title { font-size: 28px; font-weight: 700; line-height: 1.3; margin-bottom: 12px; }
.highlight { color: var(--accent); }
.hero-sub { color: var(--muted); max-width: 580px; margin: 0 auto 20px; font-size: 14px; line-height: 1.6; }
.hero-stats { display: flex; gap: 32px; justify-content: center; flex-wrap: wrap; }
.stat { text-align: center; }
.stat-val { display: block; font-size: 22px; font-weight: 700; color: var(--accent); }
.stat-label { font-size: 11px; color: var(--muted); }

.workflow-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
@media(max-width:680px) { .workflow-grid { grid-template-columns: 1fr; } }

.step-card { border-color: var(--border); }
.step-card.active { border-color: rgba(88,166,255,0.3); }

.tab-row { display: flex; gap: 4px; margin-bottom: 16px; background: var(--surface2); border-radius: 6px; padding: 3px; }
.tab-btn { flex: 1; padding: 6px; border: none; background: transparent; color: var(--muted); border-radius: 4px; cursor: pointer; font-size: 12px; transition: all .15s; }
.tab-btn.active { background: var(--surface); color: var(--text); }

.form-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media(max-width:420px) { .form-grid-2 { grid-template-columns: 1fr; } }

.drop-zone {
  border: 2px dashed var(--border); border-radius: 8px;
  padding: 28px; text-align: center; cursor: pointer;
  transition: border-color .15s, background .15s;
}
.drop-zone:hover, .drop-zone.drag-over {
  border-color: var(--accent); background: var(--accent-dim);
}
.drop-icon { font-size: 28px; margin-bottom: 8px; }
.drop-text { color: var(--text); font-size: 13px; }
.drop-hint { color: var(--muted); font-size: 11px; margin-top: 4px; }
.file-selected { display: flex; align-items: center; gap: 8px; justify-content: center; color: var(--green); }
.file-size { color: var(--muted); font-size: 12px; }
.clear-file { background: none; border: none; color: var(--red); cursor: pointer; font-size: 14px; }

.drug-info { margin-top: 12px; padding: 10px 12px; background: var(--surface2); border-radius: 6px; }
.drug-info-gene { font-size: 12px; color: var(--muted); margin-bottom: 4px; }
.drug-info-gene strong { color: var(--accent); }
.drug-info-mech { font-size: 11px; color: var(--muted); line-height: 1.5; }

.run-row { display: flex; align-items: center; gap: 20px; }
.run-btn { font-size: 15px; padding: 12px 32px; }
.cohort-ready { color: var(--green); font-size: 13px; }

.sim-list { display: flex; flex-direction: column; gap: 8px; }
.sim-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; cursor: pointer; transition: border-color .15s;
}
.sim-item:hover { border-color: var(--accent); }
.sim-item-left { display: flex; align-items: center; gap: 10px; }
.sim-drug { font-weight: 500; }
.sim-agents { color: var(--muted); font-size: 12px; }
.sim-item-right { color: var(--muted); font-size: 12px; display: flex; align-items: center; gap: 8px; }
.arrow { color: var(--accent); }
</style>
