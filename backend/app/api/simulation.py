"""
Simulation API — trigger runs, poll status, fetch results.
"""

from __future__ import annotations

import uuid
from flask import Blueprint, request, jsonify, current_app

from app.services.swarm.simulation_engine import SimulationEngine, get_simulation, list_simulations
from app.utils.logger import get_logger

simulation_bp = Blueprint("simulation", __name__)
logger = get_logger("genomicswarm.api.simulation")

_engine: SimulationEngine | None = None


def get_engine() -> SimulationEngine:
    global _engine
    if _engine is None:
        api_key = current_app.config.get("ANTHROPIC_API_KEY", "")
        model = current_app.config.get("CLAUDE_MODEL", "claude-sonnet-4-6")
        workers = current_app.config.get("SIM_WORKERS", 10)
        _engine = SimulationEngine(api_key=api_key, model=model, max_workers=workers)
    return _engine


@simulation_bp.route("/run", methods=["POST"])
def run_simulation():
    """
    Start a simulation run.
    Body JSON:
    {
        "cohort_id": "<uuid>",           # from cohort upload
        "drug": "codeine",
        "dose_mg": 30,
        "route": "oral",
        "duration_days": 14,
        "indication": "pain management",
        "comparator": "placebo",
        "max_agents": 100               # optional override
    }
    Returns { simulation_id } immediately; poll /status/<id> for progress.
    """
    from app.api.cohort import get_cohort_personas

    data = request.get_json() or {}
    cohort_id = data.get("cohort_id")

    if not cohort_id:
        return jsonify({"error": "cohort_id required"}), 400

    personas = get_cohort_personas(cohort_id)
    if personas is None:
        return jsonify({"error": f"Cohort '{cohort_id}' not found"}), 404

    max_agents = min(
        int(data.get("max_agents", len(personas))),
        current_app.config.get("MAX_AGENTS", 1000),
    )
    personas = personas[:max_agents]

    trial_config = {
        "drug": data.get("drug", "codeine"),
        "dose_mg": float(data.get("dose_mg", 30.0)),
        "route": data.get("route", "oral"),
        "duration_days": int(data.get("duration_days", 14)),
        "indication": data.get("indication", "unspecified"),
        "comparator": data.get("comparator", "placebo"),
    }

    sim_id = str(uuid.uuid4())
    engine = get_engine()
    engine.run_async(sim_id, personas, trial_config)

    logger.info(f"Simulation {sim_id} started: {len(personas)} agents, {trial_config['drug']}")
    return jsonify({
        "simulation_id": sim_id,
        "status": "running",
        "total_agents": len(personas),
        "trial_config": trial_config,
    }), 202


@simulation_bp.route("/status/<sim_id>", methods=["GET"])
def simulation_status(sim_id: str):
    """Poll simulation progress."""
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404

    completed = sim.get("completed_agents", 0)
    total = sim.get("total_agents", 1)
    progress_pct = round(100 * completed / total) if total else 0

    return jsonify({
        "simulation_id": sim_id,
        "status": sim.get("status"),
        "progress_pct": progress_pct,
        "completed_agents": completed,
        "total_agents": total,
        "started_at": sim.get("started_at"),
        "completed_at": sim.get("completed_at"),
        "error": sim.get("error"),
        # Include stats if done
        "statistics": sim.get("statistics") if sim.get("status") == "completed" else None,
    })


@simulation_bp.route("/result/<sim_id>", methods=["GET"])
def simulation_result(sim_id: str):
    """Fetch full simulation result (once completed)."""
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404
    if sim.get("status") != "completed":
        return jsonify({"error": "Simulation not yet complete", "status": sim.get("status")}), 202

    # Return result without raw agent_results blob (use /agents for that)
    return jsonify({
        "simulation_id": sim_id,
        "status": sim["status"],
        "trial_config": sim["trial_config"],
        "statistics": sim["statistics"],
        "population_analysis": sim["population_analysis"],
        "started_at": sim["started_at"],
        "completed_at": sim["completed_at"],
        "total_agents": sim["total_agents"],
    })


@simulation_bp.route("/result/<sim_id>/agents", methods=["GET"])
def simulation_agents(sim_id: str):
    """Fetch paginated agent-level results."""
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404

    results = sim.get("agent_results", [])
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    return jsonify({
        "total": len(results),
        "results": results[offset:offset + limit],
    })


@simulation_bp.route("/list", methods=["GET"])
def list_sims():
    """List all simulations (summaries only)."""
    return jsonify({"simulations": list_simulations()})
