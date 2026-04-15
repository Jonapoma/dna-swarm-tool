import { defineStore } from 'pinia'
import axios from 'axios'

const API = '/api'

export const useSimulationStore = defineStore('simulation', {
  state: () => ({
    cohortId: null,
    cohortMeta: null,
    simulationId: null,
    simulationStatus: null,   // running | completed | failed
    progress: 0,
    totalAgents: 0,
    completedAgents: 0,
    statistics: null,
    populationAnalysis: null,
    agentResults: [],
    trialConfig: null,
    error: null,
    loading: false,
    drugs: [],
    populations: [],
    pollTimer: null,
  }),

  actions: {
    async fetchDrugs() {
      const { data } = await axios.get(`${API}/drugs`)
      this.drugs = data.drugs
    },

    async fetchPopulations() {
      const { data } = await axios.get(`${API}/populations`)
      this.populations = data.populations
    },

    async uploadCohort(file, drug, dose_mg) {
      this.loading = true
      this.error = null
      try {
        const form = new FormData()
        form.append('file', file)
        form.append('drug', drug)
        form.append('dose_mg', dose_mg)
        const { data } = await axios.post(`${API}/cohort/upload`, form)
        this.cohortId = data.cohort_id
        this.cohortMeta = data
        return data
      } catch (e) {
        this.error = e.response?.data?.error || e.message
        throw e
      } finally {
        this.loading = false
      }
    },

    async createSyntheticCohort({ drug, dose_mg, n_agents, population, seed }) {
      this.loading = true
      this.error = null
      try {
        const { data } = await axios.post(`${API}/cohort/synthetic`, {
          drug, dose_mg, n_agents, population, seed
        })
        this.cohortId = data.cohort_id
        this.cohortMeta = data
        return data
      } catch (e) {
        this.error = e.response?.data?.error || e.message
        throw e
      } finally {
        this.loading = false
      }
    },

    async startSimulation(trialConfig) {
      this.loading = true
      this.error = null
      this.simulationStatus = null
      this.statistics = null
      this.populationAnalysis = null
      this.agentResults = []
      try {
        const { data } = await axios.post(`${API}/simulation/run`, {
          cohort_id: this.cohortId,
          ...trialConfig,
        })
        this.simulationId = data.simulation_id
        this.simulationStatus = 'running'
        this.totalAgents = data.total_agents
        this.trialConfig = data.trial_config
        this._startPolling()
        return data
      } catch (e) {
        this.error = e.response?.data?.error || e.message
        this.simulationStatus = 'failed'
        throw e
      } finally {
        this.loading = false
      }
    },

    _startPolling() {
      if (this.pollTimer) clearInterval(this.pollTimer)
      this.pollTimer = setInterval(async () => {
        await this._pollStatus()
      }, 2000)
    },

    async _pollStatus() {
      if (!this.simulationId) return
      try {
        const { data } = await axios.get(`${API}/simulation/status/${this.simulationId}`)
        this.simulationStatus = data.status
        this.progress = data.progress_pct
        this.completedAgents = data.completed_agents
        this.totalAgents = data.total_agents

        if (data.status === 'completed') {
          clearInterval(this.pollTimer)
          await this._fetchResults()
        } else if (data.status === 'failed') {
          clearInterval(this.pollTimer)
          this.error = data.error || 'Simulation failed'
        }
      } catch (e) {
        // ignore transient poll errors
      }
    },

    async _fetchResults() {
      const { data } = await axios.get(`${API}/simulation/result/${this.simulationId}`)
      this.statistics = data.statistics
      this.populationAnalysis = data.population_analysis
      this.trialConfig = data.trial_config

      const agentsResp = await axios.get(`${API}/simulation/result/${this.simulationId}/agents?limit=200`)
      this.agentResults = agentsResp.data.results
    },

    reset() {
      if (this.pollTimer) clearInterval(this.pollTimer)
      this.cohortId = null
      this.cohortMeta = null
      this.simulationId = null
      this.simulationStatus = null
      this.progress = 0
      this.statistics = null
      this.populationAnalysis = null
      this.agentResults = []
      this.error = null
    }
  }
})
