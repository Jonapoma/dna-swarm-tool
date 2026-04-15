"""
Swarm simulation engine — orchestrates parallel patient agent execution.
"""

from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .claude_reasoner import ClaudeReasoner
from app.utils.logger import get_logger

logger = get_logger("genomicswarm.engine")

# In-memory simulation store (replace with Redis or DB for production)
_simulations: Dict[str, dict] = {}


def get_simulation(sim_id: str) -> Optional[dict]:
    return _simulations.get(sim_id)


def list_simulations() -> List[dict]:
    return [
        {k: v for k, v in sim.items() if k != "agent_results"}
        for sim in _simulations.values()
    ]


class SimulationEngine:
    """
    Runs a swarm drug trial simulation:
    1. Takes a list of patient personas
    2. Calls ClaudeReasoner for each agent in parallel
    3. Aggregates population statistics
    4. Generates population analysis via Claude
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6", max_workers: int = 10):
        self.reasoner = ClaudeReasoner(api_key=api_key, model=model)
        self.max_workers = max_workers

    # -----------------------------------------------------------------------
    # Main run method
    # -----------------------------------------------------------------------

    def run(
        self,
        personas: List[dict],
        trial_config: dict,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> dict:
        """
        Execute a full swarm simulation.

        Args:
            personas: List of patient persona dicts from persona_generator
            trial_config: {drug, dose_mg, route, duration_days, indication, comparator}
            progress_callback: Optional fn(completed, total) for progress updates

        Returns:
            Full simulation result dict
        """
        sim_id = str(uuid.uuid4())
        n = len(personas)
        started_at = datetime.utcnow().isoformat()

        logger.info(f"[{sim_id}] Starting simulation: {n} agents, drug={trial_config.get('drug')}")

        _simulations[sim_id] = {
            "id": sim_id,
            "status": "running",
            "started_at": started_at,
            "trial_config": trial_config,
            "total_agents": n,
            "completed_agents": 0,
            "agent_results": [],
            "statistics": {},
            "population_analysis": None,
            "error": None,
        }

        agent_results = []
        completed = 0

        try:
            with ThreadPoolExecutor(max_workers=min(self.max_workers, n)) as executor:
                future_to_persona = {
                    executor.submit(
                        self._run_single_agent, persona, trial_config
                    ): persona
                    for persona in personas
                }

                for future in as_completed(future_to_persona):
                    persona = future_to_persona[future]
                    try:
                        result = future.result()
                        agent_results.append(result)
                    except Exception as e:
                        logger.error(f"Agent {persona['id']} failed: {e}")
                        agent_results.append(self._error_result(persona, str(e)))

                    completed += 1
                    _simulations[sim_id]["completed_agents"] = completed
                    _simulations[sim_id]["agent_results"] = agent_results

                    if progress_callback:
                        progress_callback(completed, n)

                    if completed % 10 == 0 or completed == n:
                        logger.info(f"[{sim_id}] Progress: {completed}/{n}")

        except Exception as e:
            logger.error(f"[{sim_id}] Simulation crashed: {e}")
            _simulations[sim_id]["status"] = "failed"
            _simulations[sim_id]["error"] = str(e)
            raise

        # Aggregate statistics
        stats = self._compute_statistics(agent_results, trial_config)
        _simulations[sim_id]["statistics"] = stats

        # Population-level Claude analysis
        logger.info(f"[{sim_id}] Running population analysis...")
        population_analysis = self.reasoner.analyse_population(
            agent_results, trial_config, stats
        )
        _simulations[sim_id]["population_analysis"] = population_analysis

        _simulations[sim_id]["status"] = "completed"
        _simulations[sim_id]["completed_at"] = datetime.utcnow().isoformat()

        logger.info(f"[{sim_id}] Simulation complete. Response rate: {stats.get('response_rate_pct')}%")

        return _simulations[sim_id]

    def run_async(self, sim_id: str, personas: List[dict], trial_config: dict) -> str:
        """
        Fire-and-forget simulation in a background thread.
        Returns sim_id immediately; poll get_simulation(sim_id) for results.
        """
        import threading

        _simulations[sim_id] = {
            "id": sim_id,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "trial_config": trial_config,
            "total_agents": len(personas),
            "completed_agents": 0,
            "agent_results": [],
            "statistics": {},
            "population_analysis": None,
            "error": None,
        }

        def _run():
            try:
                n = len(personas)
                agent_results = []
                completed = 0

                with ThreadPoolExecutor(max_workers=min(self.max_workers, n)) as executor:
                    future_map = {
                        executor.submit(self._run_single_agent, p, trial_config): p
                        for p in personas
                    }
                    for future in as_completed(future_map):
                        persona = future_map[future]
                        try:
                            result = future.result()
                        except Exception as e:
                            result = self._error_result(persona, str(e))
                        agent_results.append(result)
                        completed += 1
                        _simulations[sim_id]["completed_agents"] = completed
                        _simulations[sim_id]["agent_results"] = list(agent_results)

                stats = self._compute_statistics(agent_results, trial_config)
                _simulations[sim_id]["statistics"] = stats
                _simulations[sim_id]["population_analysis"] = self.reasoner.analyse_population(
                    agent_results, trial_config, stats
                )
                _simulations[sim_id]["status"] = "completed"
                _simulations[sim_id]["completed_at"] = datetime.utcnow().isoformat()
                logger.info(f"[{sim_id}] Async simulation complete.")
            except Exception as e:
                logger.error(f"[{sim_id}] Async simulation failed: {e}")
                _simulations[sim_id]["status"] = "failed"
                _simulations[sim_id]["error"] = str(e)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return sim_id

    # -----------------------------------------------------------------------
    # Single agent execution
    # -----------------------------------------------------------------------

    def _run_single_agent(self, persona: dict, trial_config: dict) -> dict:
        """Run one patient agent through Claude and return structured result."""
        outcome = self.reasoner.predict_patient_outcome(persona, trial_config)
        return {
            "patient_id": persona["id"],
            "agent_id": persona.get("agent_id"),
            "age": persona.get("age"),
            "sex": persona.get("sex"),
            "population": persona.get("population", "Unknown"),
            "gene": persona.get("pk_pd", {}).get("gene", "unknown"),
            "phenotype": persona.get("pk_pd", {}).get("phenotype", "unknown"),
            "traits": persona.get("traits", []),
            # Outcome fields from Claude
            "efficacy_score": outcome.get("efficacy_score", 5),
            "response_category": outcome.get("response_category", "partial_response"),
            "adverse_events": outcome.get("adverse_events", []),
            "plasma_level_category": outcome.get("plasma_level_category", "therapeutic"),
            "time_to_effect_days": outcome.get("time_to_effect_days"),
            "dose_adjustment_needed": outcome.get("dose_adjustment_needed", False),
            "suggested_dose_adjustment": outcome.get("suggested_dose_adjustment", "none"),
            "clinical_narrative": outcome.get("clinical_narrative", ""),
            "trial_endpoint_met": outcome.get("trial_endpoint_met", True),
            "discontinuation_reason": outcome.get("discontinuation_reason"),
            "confidence": outcome.get("confidence", "medium"),
            "_fallback": outcome.get("_fallback", False),
            "_tokens_used": outcome.get("_tokens_used", 0),
        }

    def _error_result(self, persona: dict, error_msg: str) -> dict:
        return {
            "patient_id": persona["id"],
            "agent_id": persona.get("agent_id"),
            "gene": persona.get("pk_pd", {}).get("gene", "unknown"),
            "phenotype": persona.get("pk_pd", {}).get("phenotype", "unknown"),
            "efficacy_score": 5,
            "response_category": "partial_response",
            "adverse_events": [],
            "plasma_level_category": "therapeutic",
            "trial_endpoint_met": True,
            "confidence": "low",
            "_error": error_msg,
        }

    # -----------------------------------------------------------------------
    # Statistics
    # -----------------------------------------------------------------------

    def _compute_statistics(self, results: List[dict], trial_config: dict) -> dict:
        """Compute population-level statistics from agent results."""
        n = len(results)
        if n == 0:
            return {}

        # Overall
        efficacy_scores = [r["efficacy_score"] for r in results if "efficacy_score" in r]
        endpoints_met = [r for r in results if r.get("trial_endpoint_met")]
        all_adrs = []
        for r in results:
            all_adrs.extend(r.get("adverse_events", []))

        # By phenotype
        phenotype_breakdown: Dict[str, dict] = {}
        for r in results:
            phen = r.get("phenotype", "unknown")
            if phen not in phenotype_breakdown:
                phenotype_breakdown[phen] = {
                    "n": 0, "efficacy_sum": 0, "endpoints_met": 0,
                    "adverse_events": 0, "discontinued": 0, "response_categories": {}
                }
            d = phenotype_breakdown[phen]
            d["n"] += 1
            d["efficacy_sum"] += r.get("efficacy_score", 5)
            if r.get("trial_endpoint_met"):
                d["endpoints_met"] += 1
            if r.get("adverse_events"):
                d["adverse_events"] += 1
            if r.get("discontinuation_reason"):
                d["discontinued"] += 1
            cat = r.get("response_category", "unknown")
            d["response_categories"][cat] = d["response_categories"].get(cat, 0) + 1

        # Compute averages per phenotype
        for phen, d in phenotype_breakdown.items():
            d["mean_efficacy"] = round(d["efficacy_sum"] / d["n"], 2) if d["n"] else 0
            d["response_rate_pct"] = round(100 * d["endpoints_met"] / d["n"], 1) if d["n"] else 0
            d["adr_rate_pct"] = round(100 * d["adverse_events"] / d["n"], 1) if d["n"] else 0
            d["discontinuation_rate_pct"] = round(100 * d["discontinued"] / d["n"], 1) if d["n"] else 0

        # ADR frequency
        adr_freq: Dict[str, int] = {}
        for adr in all_adrs:
            adr_freq[adr] = adr_freq.get(adr, 0) + 1
        top_adrs = sorted(adr_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # Response category distribution
        response_dist: Dict[str, int] = {}
        for r in results:
            cat = r.get("response_category", "unknown")
            response_dist[cat] = response_dist.get(cat, 0) + 1

        return {
            "total_agents": n,
            "drug": trial_config.get("drug"),
            "dose_mg": trial_config.get("dose_mg"),
            "mean_efficacy_score": round(sum(efficacy_scores) / len(efficacy_scores), 2) if efficacy_scores else 0,
            "response_rate_pct": round(100 * len(endpoints_met) / n, 1),
            "total_adverse_events": len(all_adrs),
            "adr_rate_pct": round(100 * sum(1 for r in results if r.get("adverse_events")) / n, 1),
            "discontinuation_rate_pct": round(100 * sum(1 for r in results if r.get("discontinuation_reason")) / n, 1),
            "top_adverse_events": [{"event": a, "count": c, "rate_pct": round(100 * c / n, 1)} for a, c in top_adrs],
            "response_distribution": response_dist,
            "phenotype_breakdown": phenotype_breakdown,
            "total_tokens_used": sum(r.get("_tokens_used", 0) for r in results),
        }
