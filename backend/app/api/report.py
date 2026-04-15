"""
Report API — generate and download simulation reports.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, Response

from app.services.swarm.simulation_engine import get_simulation
from app.services.reports.generator import generate_html_report, generate_json_report
from app.utils.logger import get_logger

report_bp = Blueprint("report", __name__)
logger = get_logger("genomicswarm.api.report")


@report_bp.route("/<sim_id>/html", methods=["GET"])
def report_html(sim_id: str) -> Response:
    """Download a self-contained HTML report."""
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404
    if sim.get("status") != "completed":
        return jsonify({"error": "Simulation not yet complete"}), 202

    html = generate_html_report(sim)
    drug = sim.get("trial_config", {}).get("drug", "simulation").replace(" ", "_")
    filename = f"genomicswarm_{drug}_{sim_id[:8]}.html"

    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@report_bp.route("/<sim_id>/json", methods=["GET"])
def report_json(sim_id: str):
    """Download a JSON summary report."""
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404
    if sim.get("status") != "completed":
        return jsonify({"error": "Simulation not yet complete"}), 202

    report = generate_json_report(sim)
    drug = report["trial_config"].get("drug", "simulation").replace(" ", "_")
    filename = f"genomicswarm_{drug}_{sim_id[:8]}.json"

    resp = make_response(jsonify(report))
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@report_bp.route("/<sim_id>/preview", methods=["GET"])
def report_preview(sim_id: str):
    """Return HTML report inline (for iframe preview in UI)."""
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404
    if sim.get("status") != "completed":
        return jsonify({"error": "Simulation not yet complete"}), 202

    html = generate_html_report(sim)
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp
